# 2. Core vs Cloud

**Module:** Fundamentals · **Status:** ✅

Same transformation logic (same SQL, models, project structure). They differ in **how you
run it and what's built around it.**

## dbt Core — the open-source engine
- Free, open-source **command-line tool** (a Python package you install + run in terminal).
- The actual engine: reads models, compiles them, works out run order, sends commands to the
  warehouse. Everything dbt fundamentally does lives in Core; Cloud is built on top of it.
- **You own everything around it:**
  - Where it runs (laptop for dev; a server/scheduler for prod — Core has no scheduler).
  - Scheduling/orchestration → bolt on cron, Airflow, GitHub Actions.
  - Dev environment → your own editor (VS Code) + manual `dbt run/test/build`.
  - Credentials → manage yourself (`profiles.yml` + env vars).
  - Git wiring and doc hosting → yourself.
- Mental model: **Core is the engine; you build the car around it.** Max control, no license cost.

## dbt Cloud — the managed platform
- Paid, hosted **SaaS** (log in via browser; you don't install/host it).
- Runs dbt Core *for you* underneath, wrapped in a managed product. Adds:
  - **Built-in scheduler ("Jobs")** — biggest reason teams adopt Cloud.
  - Browser IDE (**dbt Studio**) with Git built in.
  - Managed credentials & Dev/Staging/Prod environments.
  - Hosted docs & lineage; CI/CD on pull requests.
  - Logging, alerting (email/Slack), audit logs, RBAC.
  - Cloud-only AI/governance: Wizard, Canvas, Insights, Catalog, Semantic Layer APIs.
- Mental model: **engine + the whole car, managed for you** — for a subscription fee.

## The relationship (commonly misunderstood)
**dbt Cloud is NOT a different/better engine.** It's dbt Core running on dbt Labs' servers,
surrounded by a managed product. A model written for Core runs unchanged on Cloud. The
difference is infrastructure + tooling + convenience, not the engine.
- Genuine engine-level exception: the new **dbt Fusion engine** (separate later topic) — a
  next-gen rewrite of the engine itself, distinct from the Core-vs-Cloud product split.

## Trade-off
| | Core | Cloud |
|---|---|---|
| Cost | Free | Paid subscription |
| Hosting | You host/maintain | Fully managed |
| Scheduling | BYO (cron/Airflow/GH Actions) | Built-in Jobs |
| Dev env | Your editor + terminal | Browser IDE (Studio) |
| Creds/envs | You manage | Managed in UI |
| Docs/lineage | Generate + host yourself | Hosted automatically |
| CI/CD, RBAC, alerting | Build yourself | Built in |
| AI features | ❌ | ✅ Cloud-only |

## One-paragraph takeaway
Core is the free open-source CLI engine that compiles/runs your SQL transformations, but you
supply everything around it. Cloud runs that *same* engine on managed servers and bundles
scheduler, browser IDE, managed envs, hosted docs, CI/CD, RBAC, alerting, and Cloud-only AI.
Same logic underneath; the choice is infrastructure ownership and convenience, not a different engine.
