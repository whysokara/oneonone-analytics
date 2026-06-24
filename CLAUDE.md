# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What This Repo Is

End-to-end analytics pipeline on top of the OneOnOne SaaS product (shared work journal for managers and direct reports). The pipeline ships in 8 weeks:

```
Supabase (source) → Python ingestion → Snowflake ONEONONE_DB.RAW
  → dbt staging layer → dbt marts → MetricFlow semantic layer
  → LangGraph agent → Next.js /api/analyst (in-app chat)
```

The source app context lives in `context-from-fullstackapp.md`. The week-by-week plan lives in `oneonone_ai_analyst_8week_plan.pdf`. Read both before making architectural decisions.

## Repo Structure (when built out)

```
ingestion/          # Python scripts: Supabase → Snowflake
.github/workflows/  # GitHub Actions cron (daily 2am IST)
dbt/                # dbt project root
  models/
    staging/        # stg_* — typed, renamed, no business logic
    marts/          # dim_*, fct_*, mart_* — business logic lives here
  tests/
  dbt_project.yml
agent/              # LangGraph AI analyst agent
  tools/            # get_metric, list_available_metrics, compare_periods, get_trend
eval/               # 20-question eval set + scoring script
```

## Commands

```bash
# Ingestion
python ingestion/ingest.py                  # full run
python ingestion/ingest.py --table entries  # single table

# dbt
dbt run                          # build all models
dbt run --select staging.*       # staging layer only
dbt run --select marts.*         # marts only
dbt test                         # run all tests
dbt build                        # run + test together
dbt build --select stg_entries   # single model

# MetricFlow
mf query --metrics mrr --group-by metric_time__month
mf query --metrics active_managers --group-by metric_time__week

# Agent eval
python eval/run_eval.py          # scores agent against 20 known-answer questions
```

## Environment Variables

```bash
# Supabase (source) — service-role key only, bypasses RLS
SUPABASE_URL=https://<project>.supabase.co
SUPABASE_SERVICE_ROLE_KEY=...

# Snowflake (destination)
SNOWFLAKE_ACCOUNT=<org>-<account>
SNOWFLAKE_USER=...
SNOWFLAKE_PASSWORD=...
SNOWFLAKE_WAREHOUSE=...
SNOWFLAKE_DATABASE=ONEONONE_DB
SNOWFLAKE_SCHEMA=RAW
```

Never use the Supabase anon key for ingestion — it silently returns empty rows on most tables due to RLS.

## Source Database — Critical Facts

**Mixed column casing:** Older tables (`users`, `boards`, `entries`, `memberships`, `announcements`, `announcement_reactions`, `support_requests`) use camelCase column names (`"updatedAt"`, `"boardId"`). Newer tables (`subscriptions`, `usage_events`) use snake_case. All staging models must normalize everything to snake_case.

**Incremental load strategy per table:**

| Table | Strategy | Key column |
|---|---|---|
| users, boards, entries, announcements, subscriptions | Incremental | `updatedAt` / `updated_at` |
| memberships, announcement_reactions, support_requests | Full refresh | — |
| usage_events | Append-only | `created_at` (never updated) |

## Business Rules (affect every mart and metric)

**Manager self-entries:** When `entries.employeeId = boards.managerId`, it's the manager logging their own work. Exclude from all team-level metrics (`entries_per_manager`, `team_adoption_rate`, etc). Include in volume totals.

**Activation:** A manager is "activated" when at least one team member has at least one `published` entry. Board created ≠ activated.

**MRR:** Only `subscriptions` where `status = 'active'` AND `is_complimentary = false`. Free plan = $0 MRR. Complimentary rows have both `is_complimentary = true` and `status = 'complimentary'` — check both.

**Financial year:** April–March. Q1 = Apr–Jun, Q2 = Jul–Sep, Q3 = Oct–Dec, Q4 = Jan–Mar. Use for all quarterly business metrics. Exception: `usage_events` quota tracking uses calendar quarters — do not mix these.

**Entry lifecycle:** `draft` → `pending_approval` → `published`. Once `published`, status is immutable. JSON imports land directly at `published`. `pending_approval` → `draft` = manager returned the entry.

**`entryDate` vs `createdAt`:** Use `entryDate` (when the work happened) for all business metrics. Use `createdAt` (when it was logged) for pipeline/audit only.

## Mart Data Models

- `dim_managers` — one row per manager: plan, team size, activation status, signup date
- `dim_teams` — one row per board: team size, creation date, manager plan
- `fct_entries` — one row per entry: category, approval status, `is_first_entry` flag
- `fct_subscriptions` — one row per subscription event: MRR contribution, transition type
- `mart_manager_health` — daily churn signal: entry frequency + team size + last activity + plan

## MetricFlow Metrics (10 total)

`total_managers`, `new_managers_mtd`, `active_managers`, `entries_per_manager`, `team_adoption_rate`, `mrr`, `conversion_rate`, `churn_rate`, `avg_team_size`, `feature_adoption`

Each metric has dimensions: `plan`, `date`, `role`, `category` where applicable.

## LangGraph Agent Tools

| Tool | Purpose |
|---|---|
| `get_metric(name, time_grain, filters)` | Query a MetricFlow metric |
| `list_available_metrics()` | Returns all 10 metrics with descriptions |
| `compare_periods(metric, period_1, period_2)` | MoM / QoQ comparisons |
| `get_trend(metric, last_n_days)` | Daily/weekly trend data |

Agent must scope answers per manager (a manager can only query their own team's data). Every answer must include a citation: metric name | source table | last refreshed timestamp.

## Reliability Constraints

- MRR cannot be negative
- Active managers cannot exceed total managers
- Churn rate cannot exceed 100%
- If the agent cannot map a question to a metric with high confidence → return "I don't have a metric for that yet"
- Eval target: 17+/20 on the 20-question eval set
