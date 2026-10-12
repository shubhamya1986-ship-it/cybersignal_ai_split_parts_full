# CyberSignal AI — Split JSON Dataset Version

This version is designed for the take-home dataset already split into files:

```text
project/
├── data/
│   └── dataset_parts/
│       ├── part_01.jsonl
│       ├── part_02.jsonl
│       ├── part_03.jsonl
│       └── ...
├── app/
├── scripts/
├── prompts/
├── skills/
└── evals/
```

You do NOT need the original 11 GB file.

The pipeline automatically discovers every `.json` or `.jsonl` file inside:

`data/dataset_parts/`

It processes one file at a time and one record at a time, so it does not load the entire dataset into RAM.

## Run

```bash
pip install -r requirements.txt
python scripts/profile_parts.py
python scripts/ingest_parts.py
python scripts/build_accounts.py
python scripts/build_scores.py
streamlit run app/streamlit_app.py
```

## If your folder is exactly

```text
data/dataset_parts/part1.json
data/dataset_parts/part2.json
...
```

you do not need to change any path.

## Supported JSON layouts

The ingestion script supports:

1. JSON Lines / NDJSON:

```text
{"org":"A", ...}
{"org":"B", ...}
{"org":"C", ...}
```

2. A JSON array:

```json
[
  {"org":"A", ...},
  {"org":"B", ...}
]
```

The array reader is also incremental and does not require loading the whole array into memory.

## Main design

```text
data/dataset_parts/*.json / *.jsonl
          |
          v
incremental JSON parser
          |
          v
DuckDB observations
          |
          v
account aggregation
          |
          v
deterministic security score
          |
          +------> Streamlit
          |
          +------> FastAPI
          |
          v
evidence-grounded LLM
          |
          +------> account brief
          +------> outreach
          +------> trace
          |
          v
evaluation harness
```

## Important

Internet exposure is not proof of vulnerability, compromise, or breach.

The score is therefore called:

**Cybersecurity Priority Score**

not "probability of purchase" or "probability of breach".
