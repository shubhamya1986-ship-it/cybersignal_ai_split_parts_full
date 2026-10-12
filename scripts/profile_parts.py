from pathlib import Path
from collections import Counter
import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from scripts.json_stream import iter_json_records

ROOT = Path(__file__).resolve().parents[1]
PARTS = ROOT / "data" / "dataset_parts"

def main():
    files = sorted(list(PARTS.glob("*.json")) + list(PARTS.glob("*.jsonl")))
    if not files:
        raise SystemExit(f"No JSON files found in {PARTS}")

    orgs=Counter()
    ports=Counter()
    products=Counter()
    tags=Counter()
    countries=Counter()
    total=0

    print(f"Found {len(files)} dataset parts")
    for path in files:
        count=0
        for x in iter_json_records(path):
            count += 1
            total += 1
            orgs[str(x.get("org") or x.get("isp") or "Unknown")] += 1
            if x.get("port") is not None:
                ports[str(x["port"])] += 1
            if x.get("product"):
                products[str(x["product"])] += 1
            for t in x.get("tags") or []:
                tags[str(t)] += 1
            loc=x.get("location") or {}
            if isinstance(loc,dict) and loc.get("country"):
                countries[str(loc["country"])] += 1
        print(f"{path.name}: {count:,} records")

    print(f"\nTOTAL RECORDS: {total:,}")
    print("\nTop organizations:")
    for k,v in orgs.most_common(20): print(f"{v:,}\t{k}")
    print("\nTop ports:")
    for k,v in ports.most_common(20): print(f"{v:,}\t{k}")
    print("\nTop products:")
    for k,v in products.most_common(20): print(f"{v:,}\t{k}")
    print("\nTop tags:")
    for k,v in tags.most_common(20): print(f"{v:,}\t{k}")
    print("\nTop countries:")
    for k,v in countries.most_common(20): print(f"{v:,}\t{k}")

if __name__=="__main__":
    main()
