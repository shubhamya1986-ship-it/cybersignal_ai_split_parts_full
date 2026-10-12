# Planning

## Product goal

Prioritize organizations that show stronger observable cybersecurity-relevant internet exposure.

## Available data

The split JSON files contain infrastructure observations such as organization, IP, port, timestamp, location, product, tags, cloud and HTTP metadata.

## Missing data

The dataset may not provide:
- industry
- employee count
- revenue
- existing cybersecurity vendor
- buying committee
- CRM stage
- actual purchase intent

Therefore the product does not pretend to calculate true purchase probability.

## Sales workflow

Filter -> prioritize -> inspect evidence -> review unknowns -> AI account brief -> AI outreach -> human review.

## Success metrics

- Precision/recall/F1 on 20–30 hand-labelled accounts
- AI groundedness
- LLM latency
- LLM cost per account
- downstream meeting/reply rate when CRM outcomes become available
