# OneOnOne Analytics

End-to-end analytics pipeline on top of the [OneOnOne](https://github.com/whysokara/oneonone) SaaS product — a shared work journal for managers and their teams.

## Architecture

```
Supabase (live app data)
  → seed_data  →  Python ingestion  →  Snowflake ONEONONE_DB.RAW
  → dbt staging (typed)  →  dbt intermediate (reusable joins)  →  dbt marts (business logic)
  → MetricFlow semantic layer (10 metrics)
  → LangGraph AI analyst agent
  → /api/analyst (in-app chat inside OneOnOne)
```

**Orchestration:** [Dagster](https://dagster.io) runs `seed → ingest → dbt` as one
connected asset graph (dbt tests surface as asset checks), scheduled daily at 11:00 IST.
The graph and run history are visible in the Dagster UI (`dagster dev`).

## Stack

| Layer | Tool |
|---|---|
| Source | Supabase (Postgres) |
| Ingestion | Python (Supabase → Snowflake) |
| Orchestration | Dagster (assets, schedule, lineage) |
| Destination | Snowflake |
| Transformation | dbt (staging / intermediate / marts) + MetricFlow |
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
# Orchestration (Dagster) — the normal way to run the pipeline
.venv/bin/dagster dev -f orchestration/definitions.py                            # local UI at localhost:3000
.venv/bin/dagster job execute -f orchestration/definitions.py -j daily_pipeline  # run full pipeline (seed → ingest → dbt), no UI
# After changing dbt models, refresh the manifest so Dagster sees them:
cd transform && dbt parse

# Run the underlying steps directly (without Dagster)
python ingestion/seed_data.py      # append seed rows to Supabase
python ingestion/ingest.py         # Supabase → Snowflake RAW
dbt build                          # run all models + tests
dbt build --select stg_entries     # single model

# MetricFlow
mf query --metrics mrr --group-by metric_time__month

# Eval
python eval/run_eval.py
```

> Note: use `.venv/bin/dagster` (explicit path) if you use pyenv — its shims can
> shadow the venv's `dagster` even when the venv looks active.

## Project Structure

```
ingestion/          # Supabase → Snowflake Python scripts (ingest, seed_data, db)
transform/          # dbt project
  models/
    staging/        # stg_* — clean types, snake_case, no business logic
    intermediate/   # int_* — reusable joins/derivations shared across marts
    marts/          # dim_*, fct_*, mart_* — business logic
orchestration/      # Dagster code location (assets, daily_pipeline job, schedule)
agent/              # LangGraph AI analyst
eval/               # 20-question eval set + scoring script
snowflake/          # setup.sql / teardown.sql — warehouse, DB, schemas, RBAC
```
