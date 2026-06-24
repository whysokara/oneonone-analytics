# Improvements Backlog

"Good to have" items not yet implemented — engineering maturity gaps identified after Week 1. Prioritized. Pull from the top.

Legend: 🔴 correctness · 🟡 robustness/scale · 🟢 observability/ops · 🔵 security/repo · ✅ done

---

## Priority order (recommended)

### 🔴 Tier 1 — Correctness
1. ✅ **Supabase 1000-row pagination** — `fetch_table` was truncating `entries` (1863 → 1000). Fixed via `.range()` pagination on 2026-06-25. See ISSUES_LOG #10.
2. ⬜ **Job lies on partial failure.** `ingest.py` wraps each table in `try/except` that prints and continues, then exits `0`. If one table fails, GitHub Actions still shows green. → Track failures, exit non-zero if any table failed.
3. ⬜ **No atomicity.** `DROP → CREATE → INSERT` means a mid-run crash leaves a table empty/half-loaded. → Load into a temp table, then atomic swap (or wrap in a transaction).

### 🟡 Tier 2 — Robustness & scale
4. ⬜ **Incremental loading** (deliberately deferred). Full-refresh every run; fine at 1k rows, needed at scale. Use `updated_at` watermark per the per-table strategy in CLAUDE.md.
5. ⬜ **Bulk loading.** Row-by-row `executemany` is slow at scale. Switch to `write_pandas` (PUT + `COPY INTO`).
6. ⬜ **Retries** with backoff on transient Supabase/Snowflake failures.
7. ⬜ **Row-count reconciliation** as an automated post-load check (Supabase `count='exact'` == Snowflake count, else fail). This is exactly what caught issue #10 manually.

### 🟢 Tier 3 — Observability & ops
8. ⬜ **Real logging** (the `logging` module: levels, timestamps, structure) instead of `print()`.
9. ⬜ **Failure alerting** beyond GitHub's default email (e.g. Slack webhook on cron failure).
10. ⬜ **Ingestion audit table** in Snowflake — run timestamp, rows per table, success/fail. Your own run history.

### 🔵 Tier 4 — Security & reproducibility
11. ⬜ **Key-pair auth for the service user** instead of password. Snowflake is deprecating password auth for programmatic/service accounts; key-pair is the recommended CI path.
12. ⬜ **Dependency lock file** (`pip freeze > requirements.lock`). We loosened to `>=` ranges (issue #1), so installs aren't reproducible yet.

### Tier 5 — Repo maturity
13. ⬜ Unit tests for ingestion logic.
14. ⬜ CI linting (ruff/black) on push.

---

## Notes
- **Top 3 to tackle next:** #2 (fail-loud), #11 (key-pair auth), #12 (lock file) — highest signal for correctness + security.
- #1 already done. #4 (incremental) is a conscious deferral, not an oversight — revisit when row counts grow or to demo the watermark pattern.
