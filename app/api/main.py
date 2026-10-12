from pathlib import Path
import sys
import pandas as pd
from fastapi import FastAPI,HTTPException

ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT))

from app.scoring.scorer import account_context
from app.llm.account_intel import explain,outreach

app=FastAPI(title="CyberSignal AI",version="1.0")
DATA=ROOT/"data"/"accounts_scored.parquet"

def load():
    if not DATA.exists():
        raise HTTPException(500,"Run the data pipeline first")
    return pd.read_parquet(DATA)

@app.get("/health")
def health():
    return {"status":"ok"}

@app.get("/accounts")
def accounts(priority:str|None=None,min_score:float=0):
    df=load()
    if priority:
        df=df[df.priority.str.lower()==priority.lower()]
    df=df[df.score>=min_score].sort_values("score",ascending=False)
    return df.head(200).fillna("").to_dict("records")

@app.get("/accounts/{org}")
def account(org:str):
    df=load()
    x=df[df.org==org]
    if x.empty:
        raise HTTPException(404,"Account not found")
    return account_context(x.iloc[0])

@app.post("/accounts/{org}/explain")
def explain_api(org:str):
    return explain(account(org))

@app.post("/accounts/{org}/outreach")
def outreach_api(org:str):
    return outreach(account(org))
