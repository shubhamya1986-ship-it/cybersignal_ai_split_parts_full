from pathlib import Path
import argparse,json,sys

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from app.scoring.rules import score_account

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--input",default=str(ROOT/"evals"/"hand_labeled.jsonl"))
    ap.add_argument("--prompt-version",default="v2")
    args=ap.parse_args()

    rows=[json.loads(x) for x in open(args.input,encoding="utf-8") if x.strip()]
    y=[]
    p=[]
    for row in rows:
        _,priority,_,_=score_account(row["account"])
        y.append(row["label"].lower())
        p.append(priority.lower())

    print("Prompt version:",args.prompt_version)
    print("Examples:",len(rows))

    for cls in ["low","medium","high"]:
        tp=sum(a==cls and b==cls for a,b in zip(y,p))
        fp=sum(a!=cls and b==cls for a,b in zip(y,p))
        fn=sum(a==cls and b!=cls for a,b in zip(y,p))
        precision=tp/(tp+fp) if tp+fp else 0
        recall=tp/(tp+fn) if tp+fn else 0
        f1=2*precision*recall/(precision+recall) if precision+recall else 0
        print(f"{cls}: precision={precision:.3f} recall={recall:.3f} f1={f1:.3f}")

    accuracy=sum(a==b for a,b in zip(y,p))/len(y) if y else 0
    print(f"accuracy={accuracy:.3f}")

if __name__=="__main__":
    main()
