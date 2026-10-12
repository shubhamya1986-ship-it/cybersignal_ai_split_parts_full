from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PARTS = ROOT / "data" / "dataset_parts"

print("Project root :", ROOT)
print("Dataset path :", PARTS)
print("Exists       :", PARTS.exists())

if not PARTS.exists():
    raise SystemExit("Dataset folder does not exist.")

files = sorted(list(PARTS.glob("*.json")) + list(PARTS.glob("*.jsonl")))

print("Found files  :", len(files))
for f in files[:20]:
    print(" -", f.name)

if len(files) > 20:
    print(f"... and {len(files)-20} more")

if not files:
    print("\nNo .json/.jsonl files found.")
    print("Make sure the files are physically inside:")
    print(PARTS)
else:
    print("\nDataset parts look correctly placed.")
