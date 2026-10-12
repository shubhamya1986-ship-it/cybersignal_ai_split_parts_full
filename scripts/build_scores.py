from pathlib import Path
import sys, pandas as pd

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))

from app.scoring.rules import score_account

def main():
    inp=ROOT/"data"/"accounts.parquet"
    out=ROOT/"data"/"accounts_scored.parquet"

    if not inp.exists():
        raise SystemExit("accounts.parquet not found. Run scripts/build_accounts.py first.")

    df=pd.read_parquet(inp)
    results=df.apply(score_account,axis=1,result_type="expand")
    results.columns=["score","priority","signals","why_now"]
    outdf=pd.concat([df,results],axis=1)
    outdf.to_parquet(out,index=False)

    print(f"Wrote {out}")
    print(outdf["priority"].value_counts())

if __name__=="__main__":
    main()
