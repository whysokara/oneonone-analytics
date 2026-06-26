# CLAUDE.md — oneonone-analytics

This file is read by Claude Code at the start of every session.
Read `context-from-fullstackapp.md` and `oneonone_ai_analyst_8week_plan.pdf` before making any architectural decisions.

---

## What This Repo Is

End-to-end analytics pipeline on top of OneOnOne — a SaaS product for manager-reportee
performance tracking. Source data lives in Supabase (Postgres). This repo owns everything
from raw ingestion to the AI analyst agent.

```
Supabase (source)
  → Python ingestion (incremental, GitHub Actions cron)
  → Snowflake ONEONONE_DB.RAW
  → dbt staging layer       (stg_* — typed, renamed, no business logic)
  → dbt marts               (dim_*, fct_*, mart_* — business logic)
  → MetricFlow semantic layer (10 business metrics)
  → LangGraph agent          (4 tools, per-manager scoping)
  → Next.js /api/analyst     (in-app chat interface in the fullstack app)
```

---

## Repo Structure

```
oneonone-analytics/
├── ingestion/                  # Python: Supabase → Snowflake
│   └── ingest.py
├── dbt/                        # dbt project root
│   ├── models/
│   │   ├── staging/            # stg_* — one model per source table
│   │   │   ├── _sources.yml
│   │   │   └── _schema.yml
│   │   ├── marts/              # dim_*, fct_*, mart_*
│   │   │   └── _schema.yml
│   │   └── metrics/            # MetricFlow metric definitions
│   ├── tests/                  # custom singular tests
│   ├── macros/                 # reusable Jinja macros
│   ├── snapshots/              # SCD Type 2 if needed
│   ├── seeds/                  # static reference data only
│   ├── dbt_project.yml
│   └── profiles.yml
├── agent/                      # LangGraph AI analyst
│   ├── tools/                  # get_metric, list_available_metrics, compare_periods, get_trend
│   └── graph.py
├── eval/                       # 20-question eval set + scoring script
│   ├── eval_set.json
│   └── run_eval.py
├── .github/
│   └── workflows/
│       └── ingest.yml          # daily cron 2am IST
├── .venv/                      # gitignored
├── requirements.txt
├── .env.example
└── CLAUDE.md                   # this file
```

---

## Commands

```bash
# Environment
source .venv/bin/activate

# Ingestion
python ingestion/ingest.py                   # full run
python ingestion/ingest.py --table entries   # single table

# dbt
dbt run                                      # build all models
dbt run --select staging.*                   # staging layer only
dbt run --select marts.*                     # marts only
dbt test                                     # run all tests
dbt build                                    # run + test together
dbt build --select stg_entries               # single model

# MetricFlow
# IMPORTANT: always prefix mf commands with DBT_PROFILES_DIR=~/.dbt
# (dbt-metricflow 0.13.0 + dbt-core 1.11 version mismatch — mf can't find profiles without it)
DBT_PROFILES_DIR=~/.dbt mf health-checks
DBT_PROFILES_DIR=~/.dbt mf query --metrics mrr --group-by metric_time__month
DBT_PROFILES_DIR=~/.dbt mf query --metrics active_managers --group-by metric_time__week
DBT_PROFILES_DIR=~/.dbt mf validate-configs

# Agent eval
python eval/run_eval.py                      # scores agent against 20 known-answer questions
```

---

## Environment Variables

```bash
# Supabase — always use service-role key, never anon key
# Anon key silently returns empty rows on most tables due to RLS
SUPABASE_URL=https://<project>.supabase.co
SUPABASE_SERVICE_ROLE_KEY=...

# Snowflake
SNOWFLAKE_ACCOUNT=<org>-<account>
SNOWFLAKE_USER=...
SNOWFLAKE_PASSWORD=...
SNOWFLAKE_WAREHOUSE=ONEONONE_WH
SNOWFLAKE_DATABASE=ONEONONE_DB
SNOWFLAKE_SCHEMA=RAW
```

---

## Source Schema — Critical Facts

### Column Casing (mixed — normalize everything in staging)
- Older tables (`users`, `boards`, `entries`, `memberships`, `announcements`,
  `announcement_reactions`, `support_requests`) use **camelCase** (`"updatedAt"`, `"boardId"`)
- Newer tables (`subscriptions`, `usage_events`) use **snake_case**
- All staging models must normalize everything to `snake_case`

### Incremental Strategy Per Table

| Table | Strategy | Key Column |
|---|---|---|
| users, boards, entries, announcements, subscriptions | Incremental | `updatedAt` / `updated_at` |
| memberships, announcement_reactions, support_requests | Full refresh | — |
| usage_events | Append-only | `created_at` (never updated) |

---

## Business Rules

These rules affect every mart and metric. Never deviate without asking.

**Manager self-entries**
When `entries.employeeId = boards.managerId`, the manager is logging their own work.
Exclude from all team-level metrics (`entries_per_manager`, `team_adoption_rate`, etc).
Include in volume totals.

**Activation**
A manager is "activated" when at least one team member has at least one `published` entry.
Board created ≠ activated. This is the north star activation signal.

**MRR**
Only `subscriptions` where `status = 'active'` AND `is_complimentary = false`.
Free plan = $0 MRR. Complimentary rows have both `is_complimentary = true`
and `status = 'complimentary'` — always check both columns.

**Financial Year**
April–March. Q1 = Apr–Jun, Q2 = Jul–Sep, Q3 = Oct–Dec, Q4 = Jan–Mar.
Use for all quarterly business metrics.
Exception: `usage_events` quota tracking uses calendar quarters — never mix these.

**Entry Lifecycle**
`draft` → `pending_approval` → `published`
Once `published`, status is immutable.
JSON imports land directly at `published`.
`pending_approval` → `draft` = manager returned the entry.

**Date Fields**
Use `entryDate` (when work happened) for all business metrics.
Use `createdAt` (when it was logged) for pipeline/audit only. Never mix these.

---

## Naming Conventions

### Models
| Layer | Pattern | Example |
|---|---|---|
| Staging | `stg_<source>__<entity>` | `stg_supabase__users` |
| Dimensions | `dim_<entity>` | `dim_managers`, `dim_teams` |
| Facts | `fct_<event>` | `fct_entries`, `fct_subscriptions` |
| Marts | `mart_<concept>` | `mart_manager_health` |
| Intermediate | `int_<description>` | `int_users_with_plan` |

### Columns
| Type | Pattern | Example |
|---|---|---|
| Primary key | `<entity>_id` | `user_id`, `board_id` |
| Foreign key | `<referenced_entity>_id` | `manager_id`, `team_id` |
| Timestamps | `<event>_at` | `created_at`, `activated_at` |
| Booleans | `is_<condition>` / `has_<condition>` | `is_active`, `has_entries` |
| Dates | `<event>_date` | `signup_date`, `churn_date` |
| Money | `<metric>_amount` | `mrr_amount` |
| Counts | `<entity>_count` | `entry_count`, `member_count` |

### Files and Snowflake Objects
- Model files: `snake_case.sql`
- YAML files: `snake_case.yml`
- One schema YAML per folder: `staging/_schema.yml`, `marts/_schema.yml`
- Snowflake identifiers: `UPPER_SNAKE_CASE`
- dbt refs and sources: `lower_snake_case`

---

## SQL Style Guide

- Use CTEs, never subqueries
- CTE names: descriptive snake_case (`managers`, `joined`, `aggregated`, `final`)
- Last CTE always named `final`, always end with `select * from final`
- Lowercase SQL keywords: `select`, `from`, `where`, `join`, `group by`
- One column per line
- Commas at the start of the line
- Explicit column names in `select` — never `select *` in marts
- Every mart model starts with a grain comment

```sql
-- grain: one row per manager, updated daily
with managers as (
    select * from {{ ref('stg_supabase__users') }}
    where user_role = 'manager'
),
boards as (
    select * from {{ ref('stg_supabase__boards') }}
),
joined as (
    select
        managers.user_id
        , managers.email
        , managers.created_at
        , boards.board_id
        , coalesce(boards.created_at, managers.created_at) as board_created_at
    from managers
    left join boards
        on managers.user_id = boards.manager_id
),
final as (
    select * from joined
)
select * from final
```

---

## Staging Model Standards

- One staging model per source table, no exceptions
- Only allowed operations: rename columns, cast types, basic null coalescing
- No joins in staging — always 1:1 with source table
- Always cast timestamps to `TIMESTAMP_TZ` (preserves the UTC offset from Supabase's `timestamptz`)
- Add `_dbt_loaded_at` using `current_timestamp()` for auditability
- Use `{{ source('supabase', 'table') }}` — never hardcode table names

```sql
with source as (
    select * from {{ source('supabase', 'users') }}
),
renamed as (
    select
        id::varchar                as user_id,
        email::varchar             as email,
        role::varchar              as user_role,
        "createdAt"::timestamp_tz  as created_at,
        "updatedAt"::timestamp_tz  as updated_at,
        current_timestamp()        as _dbt_loaded_at
    from source
)
select * from renamed
```

---

## Materialization Strategy

| Layer | Materialization | Reason |
|---|---|---|
| Staging | `view` | Always fresh, no storage cost |
| Marts (small) | `table` | Fast query, simple rebuild |
| Marts (large/complex) | `incremental` | Performance on growing tables |
| Snapshots | `snapshot` | SCD Type 2 history |

```yaml
# dbt_project.yml
models:
  oneonone_analytics:
    staging:
      +materialized: view
      +schema: staging
    marts:
      +materialized: table
      +schema: marts
```

### Incremental Model Pattern
```sql
{{
    config(
        materialized='incremental',
        unique_key='entry_id',
        incremental_strategy='delete+insert'
    )
}}

select * from {{ ref('stg_supabase__entries') }}

{% if is_incremental() %}
    where updated_at > (select max(updated_at) from {{ this }})
{% endif %}
```

---

## Testing Standards

- Every primary key: `unique` + `not_null` — non-negotiable
- Every foreign key: `not_null` + `relationships`
- Every status/enum column: `accepted_values`
- Every mart: minimum 3 tests
- Complex business logic: singular tests in `tests/` folder

```yaml
columns:
  - name: user_id
    tests:
      - unique
      - not_null
  - name: user_role
    tests:
      - accepted_values:
          values: ['manager', 'reportee']
  - name: board_id
    tests:
      - not_null
      - relationships:
          to: ref('stg_supabase__boards')
          field: board_id
```

---

## Documentation Standards

- Every model: `description:` at model level
- Every column in a mart: `description:` required
- Staging columns: description optional, primary key required
- Tags: `tags: ['staging']`, `tags: ['marts']`, `tags: ['metrics']`

---

## Snowflake-Specific Rules

- Always `TIMESTAMP_TZ` for timestamps — preserves the source UTC offset (avoid `TIMESTAMP_NTZ`/`TIMESTAMP_LTZ`, which lose or remap it)
- Use `VARCHAR` not `STRING`
- Use `NUMBER(18,2)` for monetary amounts
- Never `SELECT *` in production models — always explicit columns
- Use `{{ target.schema }}` — never hardcode schema names
- Warehouse: start `X-SMALL`, upsize only if query times are unacceptable
- Cluster keys on large fact tables: use `updated_at` or `created_at`

---

## Mart Models (Week 3)

| Model | Grain | Purpose |
|---|---|---|
| `dim_managers` | One row per manager | Plan, team size, activation status, signup date |
| `dim_teams` | One row per board | Team size, creation date, manager plan |
| `fct_entries` | One row per entry | Category, approval status, `is_first_entry` flag |
| `fct_subscriptions` | One row per subscription event | MRR contribution, transition type |
| `mart_manager_health` | One row per manager, daily | Churn signal: entry frequency + team size + last activity + plan |

---

## MetricFlow Standards (Week 4)

10 metrics total: `total_managers`, `new_managers_mtd`, `active_managers`,
`entries_per_manager`, `team_adoption_rate`, `mrr`, `conversion_rate`,
`churn_rate`, `avg_team_size`, `feature_adoption`

Dimensions per metric: `plan`, `date`, `role`, `category` where applicable.

Rules:
- Every metric must have `label:` (human-readable, used by the AI analyst)
- Every metric must have `description:` (explains business logic)
- Never duplicate a metric — use filters for variants
- Time dimensions must use `entryDate`, not `createdAt`

```yaml
metrics:
  - name: active_managers
    label: Active Managers
    description: "Managers with at least one team entry (excluding self-entries) in the last 30 days."
    type: simple
    type_params:
      measure:
        name: manager_count
        fill_nulls_with: 0
    filter: |
      {{ Dimension('manager__last_entry_days_ago') }} <= 30
```

---

## LangGraph Agent (Week 5)

| Tool | Purpose |
|---|---|
| `get_metric(name, time_grain, filters)` | Query a MetricFlow metric |
| `list_available_metrics()` | Returns all 10 metrics with descriptions |
| `compare_periods(metric, period_1, period_2)` | MoM / QoQ comparisons |
| `get_trend(metric, last_n_days)` | Daily/weekly trend data |

**Scoping:** Agent answers are scoped per manager — a manager can only query
data about their own team. Never return cross-manager data to an individual user.

**Citation format on every answer:**
```
Source: <metric_name> | <source_table> | Last refreshed: <timestamp>
```

---

## Reliability Constraints (Week 6)

These are hard rules — never bypass:
- MRR cannot be negative
- Active managers cannot exceed total managers
- Churn rate cannot exceed 100%
- Eval target: 17+/20 on the 20-question eval set
- If agent cannot map a question to a metric with high confidence →
  return "I don't have a metric for that yet" — never hallucinate a number

---

## What Claude Should Always Do

- State the grain explicitly before writing any model
- Use `{{ ref() }}` and `{{ source() }}` — never hardcode table names
- Add tests when creating a new model
- Add `description:` to new models in schema YAML
- Add `is_incremental()` guard on every incremental model
- Add new source tables to `_sources.yml` before referencing them
- Apply business rules (manager self-entries, MRR filter, activation definition) without being reminded
- Flag any model with no tests as a risk before proceeding

## What Claude Should Never Do

- Write `select *` in a mart model
- Put business logic in a staging model
- Hardcode schema, database, or table names
- Create a model without a schema YAML entry
- Skip `unique_key` on an incremental model
- Use subqueries — always CTEs
- Assume a column is not null without a test
- Write a metric without `description:` and `label:`
- Mix `entryDate` and `createdAt` for business metrics
- Mix financial year quarters with calendar year quarters
