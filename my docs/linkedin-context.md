# Context for LinkedIn Content Strategy

This document gives an LLM full context about who I am, what I've built, and what I'm building next — so it can plan a LinkedIn content journey that builds credibility, gets me visibility, and helps me land a data/analytics engineering role.

---

## Who I Am

**Name:** Kara (imhkara@gmail.com)  
**Stage:** Learning data engineering fundamentals while simultaneously shipping a real end-to-end portfolio project.  
**Background:** Builder of OneOnOne — a SaaS product for manager-reportee performance tracking. I understand the product deeply (source data, business logic, pricing, activation metrics) because I built it.  
**Goal:** Land a role as a data/analytics engineer. Build credibility and online presence on LinkedIn while learning and building in public.

---

## The Project I'm Building: OneOnOne Analytics Pipeline

A **production-grade end-to-end analytics pipeline** on top of my own SaaS product. Not a tutorial project — it runs against real live data (real users, real subscriptions, real MRR).

### Tech Stack (fully shipped, all working)

```
Supabase (PostgreSQL source, 9 tables, real production data)
  → Python ingestion (incremental, full-refresh, append-only strategies)
  → GitHub Actions cron (runs daily at 11am IST, automated)
  → Snowflake ONEONONE_DB.RAW (8 tables ingested)
  → dbt staging layer (9 models — typed, renamed, snake_case, TIMESTAMP_TZ)
  → dbt intermediate layer (3 views — joins, enrichment, current subscription)
  → dbt marts (5 tables — dim_managers, dim_teams, fct_entries, fct_subscriptions, mart_manager_health)
  → MetricFlow semantic layer (3 semantic models, 16 metrics, queryable via mf CLI)
  → LangGraph AI analyst (COMING — Week 5)
  → Next.js /api/analyst in-app chat (COMING — Week 7)
```

### What's fully live and queryable right now
- **16 metrics** queryable via `mf query` against real Snowflake data:
  - `total_managers`, `new_managers_mtd`, `active_managers`, `conversion_rate`, `avg_team_size`
  - `mrr` ($85.83 live total), `churn_rate`, `new_subscriptions`, `churn_count_metric`
  - `team_entries`, `published_entries`, `entries_per_manager`, `team_adoption_rate`, `feature_adoption`
  - `paying_managers`, `total_team_size_metric`
- **Real business rules** encoded in the pipeline:
  - Manager self-entries excluded from team metrics
  - MRR only from `status='active'` AND `is_complimentary=false`
  - Annual subscriptions normalized to monthly (`annual_price / 12`), not `monthly_price × 12` (because annual includes 2 free months)
  - Activation = a team member (not the manager) has a published entry
  - Financial year April–March for business metrics

### Data quality / engineering rigor
- 80+ dbt tests running on every build (unique, not_null, accepted_values, relationships)
- Atomic full-refresh via load-then-swap (no partial states)
- Supabase pagination (1000-row truncation fixed)
- Snowflake RBAC: least-privilege roles (LOADER, TRANSFORMER, separate users)
- `plan_pricing` seed for real subscription pricing (free $0, pro $10/mo, pro_plus $15/mo; annual discount modelled correctly)
- MetricFlow time spine (4018-day calendar table) for time-series queries
- ISSUES_LOG with 11 real bugs found and fixed with root causes documented

---

## What I'm Learning In Parallel

Studying the **dbt Core & Cloud syllabus** (Analytics with Sushil — full cohort curriculum) alongside building:

- Completed: Role of dbt, Core vs Cloud
- In progress: Project Setup, Modeling, Testing, Documentation
- Coming: Templating/Macros, Orchestration, Advanced, dbt Cloud capabilities, MetricFlow APIs

Learning notes saved in `learning/topics/` — one file per topic, with deep concept explanations.

---

## Technologies I'm Working With

| Tool | Purpose | Depth |
|---|---|---|
| **Python** | Ingestion scripts (Supabase → Snowflake), dotenv, snowflake-connector | Hands-on, production |
| **Snowflake** | Cloud data warehouse — RBAC, schemas, warehouses, clustering | Real setup, ACCOUNTADMIN → least-privilege |
| **dbt Core** | SQL transformation framework — staging, intermediate, marts, tests, docs | Production use, 9+5+3 models |
| **MetricFlow** | Semantic layer — semantic models, measures, dimensions, entities, metrics | Just shipped 16 metrics |
| **GitHub Actions** | CI/CD — daily cron ingestion | Live, runs daily |
| **Supabase** | PostgreSQL source — service-role auth, pagination, RLS | Real product source |
| **LangGraph** | AI agent framework (coming Week 5) | Planned |
| **Next.js** | In-app chat interface (coming Week 7) | Planned |

---

## Roadmap — What's Coming Next (Future Plans)

These are **not yet built**. They are planned weeks in the 8-week pipeline build. Mention them as "next" or "coming soon" in content — never as shipped.

| Week | Deliverable | Status |
|---|---|---|
| Week 5 | **LangGraph AI analyst agent** — 4 tools (`get_metric`, `list_available_metrics`, `compare_periods`, `get_trend`), per-manager scoping, 12/15 test questions correct | 🔜 Next |
| Week 6 | **Reliability layer** — 20-question eval set, confidence handling ("I don't have a metric for that yet"), sanity checks (MRR can't be negative), citation format on every answer | 🔜 Planned |
| Week 7 | **In-app chat** — `/api/analyst` route in the OneOnOne Next.js app, collapsible dashboard panel, manager-scoped answers | 🔜 Planned |
| Week 8 | **Ship & document** — README, Loom demo walkthrough, blog post, resume bullet | 🔜 Planned |

### Why the order matters (content angle)
The semantic layer (Week 4) had to be built *before* the agent (Week 5) — the agent will call `mf query` under the hood. Metrics need a trusted definition before an AI can cite them. This sequencing (data → semantics → AI) is intentional and different from most "AI on data" projects that skip the semantic layer.

---

## The Project GitHub

Repository: `whysokara/oneonone-analytics`  
Commits tell the full story of the build — every week's work, every bug fixed, every architecture decision.

Key commit messages (portfolio-worthy):
- `feat(ingestion): add Supabase → Snowflake ingestion + connection test`
- `fix(ingestion): paginate Supabase reads to avoid 1000-row truncation`
- `fix(ingestion): atomic full refresh via load-then-swap`
- `feat(transform): week 3 data model — intermediate layer + 5 marts`
- `fix(transform): replace placeholder MRR prices with real pricing seed`
- `feat(transform): complete MetricFlow semantic layer — all 16 metrics live`

---

## What Makes This Portfolio Project Stand Out

1. **Real product, real data** — not a mock dataset or tutorial. Real users, real MRR, real activation events.
2. **Built by the product owner** — I know why every business rule exists because I designed the product. The `is_self_entry` exclusion, the `is_complimentary` MRR filter, the activation definition — these come from my product knowledge, not from a brief.
3. **Every problem is documented** — 11-entry ISSUES_LOG with root causes, not just fixes. Shows debugging depth.
4. **Incrementally correct** — went from placeholder MRR ($29/$99 guesses) to real pricing (landed page + annual discount math). Shows iteration and correctness.
5. **Full stack** — ingestion → warehouse → transformation → semantic layer → (coming) AI agent → in-app chat. Not just one piece.
6. **Learning in public** — structured notes for every topic studied, tied to the real pipeline.

---

## Target Roles / Content Positioning

**Target roles:**
- Analytics Engineer
- Data Engineer
- Analytics/Data Analyst (with engineering depth)
- dbt Developer
- Data Platform Engineer

**Positioning to build on LinkedIn:**
- Builder who understands both the product and the data
- Analytics engineer who ships real end-to-end pipelines, not just tutorial projects
- Someone learning the right tools (dbt, MetricFlow, Snowflake, LangGraph) in the right order
- Transparent about the learning journey — showing the bugs, the fixes, the decisions

**Credibility signals to highlight:**
- Real live MRR number ($85.83 from real paying users)
- 80+ dbt tests passing
- MetricFlow semantic layer with 16 queryable metrics
- GitHub commit history showing week-by-week progress
- Building the AI analyst that will query these metrics (Week 5)

---

## Content Ideas (raw material to work with)

1. The moment we discovered `mf query --metrics mrr` returned $483 instead of $85.83 — and why (two copies of the same placeholder in different models)
2. Why "annual ÷ 12 ≠ monthly price" — building correct MRR normalization
3. Why I built a semantic layer before an AI agent (and why order matters)
4. MetricFlow time spine — what it is, why it exists, how we built ours
5. Supabase silently dropped 863 rows (the 1000-row pagination bug)
6. Snowflake RBAC from scratch — why ACCOUNTADMIN in `profiles.yml` is a smell
7. What a semantic model actually is (entities, dimensions, measures explained simply)
8. Why this is not a tutorial project: real business rules that only work if you know the product
9. Week 1→4 progress thread: "I'm building an end-to-end analytics pipeline on my own SaaS product. Here's week 4."
10. The difference between ETL and ELT — explained by someone doing ELT daily
11. dbt Core vs Cloud — what's actually different (after the install experience)
12. MetricFlow compatibility hell: dbt-metricflow 0.13.0 + dbt-core 1.11 = DBT_PROFILES_DIR workaround
13. How I document bugs as a portfolio signal (ISSUES_LOG concept)
14. Building the AI analyst agent (Week 5 — upcoming)
15. "Here's the SQL MetricFlow generated for `mf query --metrics entries_per_manager`" — showing the join across semantic models

---

## Tone / Voice Notes

- Honest about being a learner ("this is my first time working with MetricFlow")
- But demonstrates depth (knows why annual/12 ≠ monthly, knows what entities are for joins)
- Builds in public — shows the failures alongside the wins
- Practical, not theoretical — always tied to real code and real numbers
- Builder identity — not just learning dbt, building a real product with it
