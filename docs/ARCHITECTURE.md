# Architecture

```text
data/dataset_parts/part*.json
          |
          v
incremental JSON parser
          |
          v
DuckDB observations
          |
          v
SQL account aggregation
          |
          v
accounts.parquet
          |
          v
deterministic score
          |
          +----> Streamlit
          |
          +----> FastAPI
          |
          v
LLM explanation/outreach
          |
          +----> versioned prompts
          +----> SKILL.md
          +----> trace/cost logs
          |
          v
20–30 hand-labelled evaluation
```

## Why split files?

The application consumes the already partitioned dataset. It never needs the original 11 GB object.

## Why DuckDB?

DuckDB provides efficient local analytical storage and SQL aggregation while keeping the implementation simple.

## Why deterministic scoring?

The ranking remains auditable and reproducible. LLM output is used for synthesis rather than silently modifying the numeric score.
