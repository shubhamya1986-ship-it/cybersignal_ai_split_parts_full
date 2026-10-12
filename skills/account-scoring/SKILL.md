# Account Scoring Skill

version: 1.0.0

## Purpose

Transform internet-infrastructure observations into an auditable cybersecurity sales-priority signal.

## Inputs

- organization
- IP footprint
- ports
- technologies/products
- security-relevant service observations
- cloud observations
- IoT observations
- HTTP observations
- geography/network diversity
- recency

## Workflow

1. Ingest split JSON parts incrementally.
2. Normalize records.
3. Store observations in DuckDB.
4. Aggregate at organization level.
5. Calculate deterministic security signals.
6. Produce a 0–100 Cybersecurity Priority Score.
7. Assign Low/Medium/High.
8. Pass evidence to the LLM only for explanation/outreach.
9. Trace every LLM call.
10. Evaluate prompt changes against hand-labelled examples.

## Guardrails

Internet exposure != vulnerability.
Internet exposure != breach.
Internet exposure != compromise.

Do not invent firmographics, incidents, buying intent, named people, or security products.
