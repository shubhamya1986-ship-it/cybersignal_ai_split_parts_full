import subprocess,sys
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]

commands=[
    [sys.executable,"scripts/profile_parts.py"],
    [sys.executable,"scripts/ingest_parts.py"],
    [sys.executable,"scripts/build_accounts.py"],
    [sys.executable,"scripts/build_scores.py"],
]

for cmd in commands:
    print("\n>>>"," ".join(cmd))
    subprocess.run(cmd,cwd=ROOT,check=True)

print("\nPIPELINE COMPLETE")
print("Run: streamlit run app/streamlit_app.py")
