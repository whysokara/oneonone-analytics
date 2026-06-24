# OneOnOne Analytics

End-to-end analytics pipeline on top of the [OneOnOne](https://github.com/whysokara/oneonone) SaaS product — a shared work journal for managers and their teams.

## Architecture

```
Supabase (live app data)
  → Python ingestion script (daily via GitHub Actions)
  → Snowflake ONEONONE_DB.RAW
  → dbt staging layer (typed, normalized)
  → dbt marts (business logic)
  → MetricFlow semantic layer (10 metrics)
  → LangGraph AI analyst agent
  → /api/analyst (in-app chat inside OneOnOne)
```

## Stack

| Layer | Tool |
|---|---|
| Source | Supabase (Postgres) |
| Destination | Snowflake |
| Ingestion | Python + GitHub Actions |
| Transformation | dbt + MetricFlow |
| AI Agent | LangGraph |
| In-app chat | Next.js API route |

## Setup

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

Copy `.env.example` to `.env` and fill in credentials.

## Environment Variables

```bash
SUPABASE_URL=https://<project>.supabase.co
SUPABASE_SERVICE_ROLE_KEY=...
SNOWFLAKE_ACCOUNT=<org>-<account>
SNOWFLAKE_USER=...
SNOWFLAKE_PASSWORD=...
SNOWFLAKE_WAREHOUSE=...
SNOWFLAKE_DATABASE=ONEONONE_DB
SNOWFLAKE_SCHEMA=RAW
```

## Commands

```bash
# Run ingestion
python ingestion/ingest.py

# dbt
dbt build                          # run all models + tests
dbt build --select stg_entries     # single model
dbt test                           # tests only

# MetricFlow
mf query --metrics mrr --group-by metric_time__month

# Eval
python eval/run_eval.py
```

## Project Structure

```
ingestion/          # Supabase → Snowflake Python scripts
dbt/
  models/
    staging/        # stg_* — clean types, snake_case, no business logic
    marts/          # dim_*, fct_*, mart_* — business logic
agent/              # LangGraph AI analyst
eval/               # 20-question eval set + scoring script
.github/workflows/  # daily cron job
```
