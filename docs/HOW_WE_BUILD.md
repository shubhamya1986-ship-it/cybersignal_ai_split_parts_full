# How We Build

I designed the pipeline around the actual shape of the provided data.

The dataset is split into JSON parts, so ingestion discovers `data/dataset_parts/*.json` and processes each part sequentially. Records are parsed incrementally and inserted into DuckDB in batches.

The core security score is deterministic because sales users need to understand why an account was prioritized. The LLM is downstream of the score and uses only verified evidence to produce an account brief and outreach.

Prompt versions and a recurring `SKILL.md` make the AI workflow reproducible. The evaluation harness compares versions using hand-labelled examples.

Every LLM call is logged with model, prompt version, request, response, latency, tokens, estimated cost and decision.

The key product caveat is that internet exposure is a security-relevant signal, not proof of vulnerability, breach or compromise.

Next production steps would include firmographic enrichment, organization identity resolution, CRM feedback, calibrated propensity modeling and incremental processing.
