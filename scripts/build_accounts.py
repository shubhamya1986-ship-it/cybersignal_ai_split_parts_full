from pathlib import Path
import argparse, duckdb

ROOT=Path(__file__).resolve().parents[1]

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--db",default=str(ROOT/"data"/"cybersignal.duckdb"))
    ap.add_argument("--output",default=str(ROOT/"data"/"accounts.parquet"))
    args=ap.parse_args()

    Path(args.output).parent.mkdir(parents=True,exist_ok=True)
    con=duckdb.connect(args.db)

    q=r"""
    SELECT
        org,
        COUNT(*) AS observation_count,
        COUNT(DISTINCT ip) AS unique_ips,
        COUNT(DISTINCT port) AS unique_ports,
        COUNT(DISTINCT product) AS unique_products,
        COUNT(DISTINCT cpe) AS unique_cpes,
        COUNT(DISTINCT hostname) AS unique_hostnames,
        COUNT(DISTINCT domain) AS unique_domains,
        COUNT(DISTINCT country) AS unique_countries,
        COUNT(DISTINCT asn) AS unique_asns,
        COUNT(DISTINCT cloud_provider) AS cloud_providers,
        COUNT(*) FILTER (WHERE cloud_provider IS NOT NULL) AS cloud_observations,
        COUNT(*) FILTER (WHERE lower(tags_json) LIKE '%iot%') AS iot_observations,
        COUNT(*) FILTER (WHERE http_status IS NOT NULL) AS http_observations,
        COUNT(*) FILTER (WHERE http_status BETWEEN 400 AND 499) AS http_4xx_observations,
        COUNT(*) FILTER (
            WHERE port IN (
                21,22,23,25,53,80,110,135,139,143,443,
                445,3389,5900,8080,8443,9200,2375
            )
        ) AS sensitive_port_observations,
        COUNT(*) FILTER (
            WHERE lower(coalesce(product,'')) LIKE '%nginx%'
        ) AS nginx_observations,
        MIN(observed_at) AS first_observed_at,
        MAX(observed_at) AS last_observed_at,
        COUNT(DISTINCT part_file) AS source_parts
    FROM observations
    GROUP BY org
    ORDER BY observation_count DESC
    """

    con.execute(f"COPY ({q}) TO '{args.output}' (FORMAT PARQUET)")
    con.close()
    print(f"Wrote {args.output}")

if __name__=="__main__":
    main()
