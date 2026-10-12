from pathlib import Path
import argparse
import json
import sys

import duckdb


# ---------------------------------------------------------------------------
# Project root
# ---------------------------------------------------------------------------

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from scripts.json_stream import iter_json_records


# ---------------------------------------------------------------------------
# Database schema
# ---------------------------------------------------------------------------

SCHEMA = """
CREATE TABLE IF NOT EXISTS observations (
    part_file VARCHAR,
    org VARCHAR,
    isp VARCHAR,
    ip VARCHAR,
    port INTEGER,
    observed_at TIMESTAMP,
    country VARCHAR,
    city VARCHAR,
    latitude DOUBLE,
    longitude DOUBLE,
    product VARCHAR,
    cpe VARCHAR,
    server VARCHAR,
    http_status INTEGER,
    title VARCHAR,
    hostname VARCHAR,
    domain VARCHAR,
    tags_json VARCHAR,
    cloud_provider VARCHAR,
    cloud_region VARCHAR,
    asn VARCHAR
)
"""


# ---------------------------------------------------------------------------
# SQL
# ---------------------------------------------------------------------------

INSERT_SQL = """
INSERT INTO observations (
    part_file,
    org,
    isp,
    ip,
    port,
    observed_at,
    country,
    city,
    latitude,
    longitude,
    product,
    cpe,
    server,
    http_status,
    title,
    hostname,
    domain,
    tags_json,
    cloud_provider,
    cloud_region,
    asn
)
VALUES (
    ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?,
    ?, ?, ?, ?, ?, ?, ?, ?, ?, ?
)
"""


# ---------------------------------------------------------------------------
# Cleaning helpers
# ---------------------------------------------------------------------------

def clean_int(value):
    """Safely convert a value to integer."""
    if value is None:
        return None

    try:
        return int(value)
    except (TypeError, ValueError):
        return None


def clean_float(value):
    """Safely convert a value to float."""
    if value is None:
        return None

    try:
        return float(value)
    except (TypeError, ValueError):
        return None


# ---------------------------------------------------------------------------
# Record normalization
# ---------------------------------------------------------------------------

def normalize(record, filename):
    """
    Convert a raw JSON record into a tuple matching the observations table.
    """

    location = record.get("location") or {}
    http = record.get("http") or {}
    headers = http.get("headers") or {}
    cloud = record.get("cloud") or {}
    tags = record.get("tags") or []

    # Make sure nested objects have the expected types
    if not isinstance(location, dict):
        location = {}

    if not isinstance(http, dict):
        http = {}

    if not isinstance(headers, dict):
        headers = {}

    if not isinstance(cloud, dict):
        cloud = {}

    if not isinstance(tags, list):
        tags = [tags]

    return (
        filename,

        # Organization
        str(
            record.get("org")
            or record.get("isp")
            or "Unknown"
        ),

        # ISP
        (
            str(record.get("isp"))
            if record.get("isp") is not None
            else None
        ),

        # Network information
        (
            str(record.get("ip"))
            if record.get("ip") is not None
            else None
        ),

        clean_int(record.get("port")),

        # Timestamp
        record.get("timestamp"),

        # Location
        location.get("country"),
        location.get("city"),
        clean_float(location.get("latitude")),
        clean_float(location.get("longitude")),

        # Product information
        record.get("product"),
        record.get("cpe"),

        # HTTP information
        headers.get("Server") or http.get("server"),
        clean_int(http.get("status")),
        http.get("title"),

        # Host information
        record.get("hostname"),
        record.get("domain"),

        # Tags
        json.dumps(
            tags,
            ensure_ascii=False
        ),

        # Cloud information
        cloud.get("provider"),
        cloud.get("region"),

        # ASN
        (
            str(record.get("asn"))
            if record.get("asn") is not None
            else None
        ),
    )


# ---------------------------------------------------------------------------
# File discovery
# ---------------------------------------------------------------------------

def get_input_files(parts_dir, start_part=0):
    """
    Find JSON and JSONL files and optionally start from a specific part.
    """

    files = sorted(
        list(parts_dir.glob("*.json"))
        + list(parts_dir.glob("*.jsonl"))
    )

    if start_part > 0:
        filtered_files = []

        for path in files:
            part_name = path.stem.lower().replace("part", "")

            if part_name.isdigit():
                part_number = int(part_name)

                if part_number >= start_part:
                    filtered_files.append(path)

        files = filtered_files

    return files


# ---------------------------------------------------------------------------
# Main processing
# ---------------------------------------------------------------------------

def main():

    parser = argparse.ArgumentParser(
        description="Load JSON/JSONL dataset parts into DuckDB."
    )

    parser.add_argument(
        "--parts",
        default=str(ROOT / "data" / "dataset_parts"),
        help="Directory containing JSON/JSONL part files."
    )

    parser.add_argument(
        "--db",
        default=str(ROOT / "data" / "cybersignal.duckdb"),
        help="DuckDB database path."
    )

    parser.add_argument(
        "--batch-size",
        type=int,
        default=10_000,
        help="Number of records inserted per batch."
    )

    parser.add_argument(
        "--start-part",
        type=int,
        default=0,
        help="Start processing from this part number. "
             "0 means process all files."
    )

    args = parser.parse_args()

    # -----------------------------------------------------------------------
    # Validate arguments
    # -----------------------------------------------------------------------

    if args.batch_size <= 0:
        raise SystemExit("--batch-size must be greater than 0.")

    parts_dir = Path(args.parts)

    if not parts_dir.exists():
        raise SystemExit(
            f"Parts directory does not exist: {parts_dir}"
        )

    # -----------------------------------------------------------------------
    # Find files
    # -----------------------------------------------------------------------

    files = get_input_files(
        parts_dir,
        args.start_part
    )

    if not files:
        raise SystemExit(
            f"No JSON or JSONL files found in {parts_dir}"
        )

    # -----------------------------------------------------------------------
    # Prepare database
    # -----------------------------------------------------------------------

    db_path = Path(args.db)
    db_path.parent.mkdir(
        parents=True,
        exist_ok=True
    )

    con = duckdb.connect(str(db_path))

    try:
        # Create table
        con.execute(SCHEMA)

        grand_total = 0

        # -------------------------------------------------------------------
        # Process files
        # -------------------------------------------------------------------

        for file_index, path in enumerate(files, start=1):

            batch = []
            file_total = 0
            skipped_records = 0

            print(
                f"\n[{file_index}/{len(files)}] "
                f"Processing {path.name}"
            )

            # ---------------------------------------------------------------
            # Read records
            # ---------------------------------------------------------------

            for record in iter_json_records(path):

                try:
                    normalized_record = normalize(
                        record,
                        path.name
                    )

                    batch.append(normalized_record)

                except Exception as exc:
                    skipped_records += 1

                    # Continue processing instead of stopping the entire job
                    print(
                        f"  Warning: failed to normalize record: {exc}",
                        file=sys.stderr
                    )

                    continue

                # -----------------------------------------------------------
                # Insert batch
                # -----------------------------------------------------------

                if len(batch) >= args.batch_size:

                    con.executemany(
                        INSERT_SQL,
                        batch
                    )

                    inserted = len(batch)

                    file_total += inserted
                    grand_total += inserted

                    batch.clear()

                    if file_total % 100_000 == 0:
                        print(
                            f"  {file_total:,} records inserted"
                        )

            # ----------------------------------------------------------------
            # Insert remaining records
            # ----------------------------------------------------------------

            if batch:

                con.executemany(
                    INSERT_SQL,
                    batch
                )

                inserted = len(batch)

                file_total += inserted
                grand_total += inserted

                batch.clear()

            # ----------------------------------------------------------------
            # File summary
            # ----------------------------------------------------------------

            print(
                f"  Completed: {file_total:,} records"
            )

            if skipped_records:
                print(
                    f"  Skipped: {skipped_records:,} records"
                )

        # -------------------------------------------------------------------
        # Create indexes
        # -------------------------------------------------------------------

        print("\nCreating indexes...")

        con.execute(
            """
            CREATE INDEX IF NOT EXISTS idx_org
            ON observations(org)
            """
        )

        con.execute(
            """
            CREATE INDEX IF NOT EXISTS idx_time
            ON observations(observed_at)
            """
        )

        con.execute(
            """
            CREATE INDEX IF NOT EXISTS idx_part
            ON observations(part_file)
            """
        )

        print("Indexes created.")

    finally:
        # Always close the database connection
        con.close()

    # -----------------------------------------------------------------------
    # Final result
    # -----------------------------------------------------------------------

    print(
        f"\nDONE. Total inserted observations: "
        f"{grand_total:,}"
    )


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    main()