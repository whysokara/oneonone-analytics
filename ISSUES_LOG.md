# Issues Log

A running record of every real problem hit while building this pipeline, its root cause, and the fix. Kept as a learning artifact (and a portfolio signal — it shows how the system was debugged, not just that it works).

Format per entry: **Symptom → Root cause → Fix → Lesson.**

---

## #10 — Supabase silently truncated `entries` to 1000 rows
**Date:** 2026-06-25 · **Area:** Ingestion
- **Symptom:** Ingestion reported `entries: 1000 rows` — suspiciously round. An exact-count check showed Supabase actually had **1,863** rows; we were loading only 1,000 (46% data loss on the core fact table). Every other table was under 1000 and unaffected.
- **Root cause:** `client.table(t).select("*").execute()` in `fetch_table`. Supabase/PostgREST caps a single response at **1000 rows** by default. No error is raised — extra rows are just dropped.
- **Fix:** Paginate with `.range(offset, offset+999)` in a loop until a page returns fewer than `page_size` rows (`ingestion/ingest.py`). Small tables loop once; large tables loop as many times as needed. Future-proof for any table that grows past 1000.
- **Lesson:** "Exactly 1000 rows" is almost always a hidden pagination cap, not a coincidence. Verify ingestion completeness with an independent exact count (`count='exact'`), never trust the returned row count alone.

## #9 — Service-user creation failed with `PRIOR_USE`
**Date:** 2026-06-25 · **Area:** Snowflake / RBAC
- **Symptom:** `create_service_user.py` crashed on `ALTER USER ... SET PASSWORD` with `New password rejected by current password policy. Reason: 'PRIOR_USE'`. The user got created but the password was never printed → lost.
- **Root cause:** The script set the password **twice** with the same value — once in `CREATE USER PASSWORD=...` and again in a follow-up `ALTER`. Snowflake's policy rejects reusing the immediately prior password.
- **Fix:** Create the user with no password, then set every property (incl. password) exactly **once** via `ALTER`. A fresh random password is generated each run, so re-runs never collide. Idempotent and self-healing for the orphaned user.
- **Lesson:** Setting a value redundantly can trip policy guards. Make provisioning scripts idempotent by setting each property exactly once.

## #8 — `teardown.sql` → `setup.sql` cycle broke at connect time
**Date:** 2026-06-25 · **Area:** Snowflake / tooling
- **Symptom:** After running `teardown.sql`, re-running `setup.sql` failed before any SQL executed — the connection itself errored.
- **Root cause:** `run_sql.py` reused the ingestion connection helper, which connects *as* `ONEONONE_LOADER` *into* `ONEONONE_DB` — the very role and database that teardown had just dropped.
- **Fix:** Give `run_sql.py` its own **bare** connection (account/user/password only, default role, no database). The `USE ROLE` statements inside the `.sql` file drive everything else.
- **Lesson:** A provisioning/infrastructure tool must not depend on the objects it creates or destroys. Connect with the bare minimum and let the script set context.

## #7 — Least-privilege test falsely showed a write succeeding
**Date:** 2026-06-25 · **Area:** Snowflake / RBAC
- **Symptom:** After `USE ROLE ONEONONE_TRANSFORMER`, an `INSERT` into `RAW` (which TRANSFORMER should not be able to do) **succeeded** — looked like least privilege was broken.
- **Root cause:** Snowflake's `DEFAULT_SECONDARY_ROLES = ('ALL')`. `USE ROLE X` sets the *primary* role, but the session still carries every other granted role as a **secondary role** — including `ONEONONE_LOADER`/`ACCOUNTADMIN`, which can write.
- **Fix:** Test single-role behavior with `USE SECONDARY ROLES NONE`. With secondaries off, the write was correctly **denied**. The grant model was right all along.
- **Lesson:** To truly test one role's privileges, disable secondary roles. Otherwise you're testing the union of all the user's roles.

## #6 — Bootstrap ordering: can't connect as objects that don't exist yet
**Date:** 2026-06-25 · **Area:** Snowflake / tooling
- **Symptom:** Provisioning steps failed when the connection specified a role/warehouse/database that hadn't been created yet (and again after a teardown removed them).
- **Root cause:** Chicken-and-egg — you can't connect *as* `ONEONONE_LOADER` *into* `ONEONONE_DB` before those exist.
- **Fix:** The very first/provisioning connection uses only account/user/password and the default role; DDL (`CREATE`/`GRANT`) doesn't even need a running warehouse. `.env` is flipped to the least-privilege values *after* setup creates them.
- **Lesson:** Bootstrapping always starts from what already exists. Sequence matters: create, then switch to using.

## #5 — `SYSADMIN` couldn't `CREATE SCHEMA` in `ONEONONE_DB`
**Date:** 2026-06-25 · **Area:** Snowflake / RBAC
- **Symptom:** `setup.sql` failed: *"Insufficient privileges to operate on database 'ONEONONE_DB'. Your primary role SYSADMIN must have CREATE SCHEMA..."*
- **Root cause:** The database was created earlier during ad-hoc testing **as ACCOUNTADMIN**, so ACCOUNTADMIN owned it. When `setup.sql` switched to SYSADMIN, SYSADMIN didn't own it and couldn't add schemas.
- **Fix:** Drop the ACCOUNTADMIN-owned DB and recreate it **as SYSADMIN** (via a bare connection), so ownership sits at the right level. Then `setup.sql` ran clean.
- **Lesson:** Whoever creates an object owns it. Always create objects as the role that *should* own them — don't do ad-hoc work as ACCOUNTADMIN.

## #4 — Snowflake session showed `None.None` for database/schema
**Date:** 2026-06-24 · **Area:** Snowflake / connection
- **Symptom:** Connection test connected, but `CURRENT_DATABASE()`/`CURRENT_SCHEMA()` returned `None.None`.
- **Root cause:** `ONEONONE_DB` and the `RAW` schema didn't exist yet, so the session couldn't set them as context.
- **Fix:** Created the database and schema (later formalized in `setup.sql`).
- **Lesson:** A successful connection doesn't mean your database/schema context is valid — verify with `CURRENT_DATABASE()`.

## #3 — `INSERT` failed: invalid identifier 'ID'
**Date:** 2026-06-24 · **Area:** Ingestion
- **Symptom:** Every table's load failed: `SQL compilation error ... invalid identifier 'ID'`.
- **Root cause:** `CREATE TABLE` quoted column names (`"id"`, case-preserved), but the `INSERT` listed them unquoted. Snowflake folds unquoted identifiers to UPPERCASE, so `id` became `ID` and didn't match the quoted `"id"` column.
- **Fix:** Quote column names in the `INSERT` too, so case is consistent across create and insert.
- **Lesson:** Snowflake uppercases unquoted identifiers. Be consistent — quote everywhere or nowhere.

## #2 — `pip install` failed: No space left on device
**Date:** 2026-06-24 · **Area:** Environment
- **Symptom:** All wheels built/downloaded, then install failed with `[Errno 28] No space left on device`.
- **Root cause:** Local disk full during the final install step.
- **Fix:** Freed disk space, re-ran `pip install` (cached wheels made it fast).
- **Lesson:** Package build success ≠ install success. Watch the final step.

## #1 — Dependency resolution conflict (snowflake-connector-python)
**Date:** 2026-06-24 · **Area:** Environment
- **Symptom:** `pip install -r requirements.txt` → `ResolutionImpossible`. We pinned `snowflake-connector-python==3.12.4`, but `dbt-snowflake==1.9.3` required a newer version.
- **Root cause:** Two packages depended on the same third package with incompatible exact pins.
- **Fix:** Loosen pins to `>=` minimum versions and let pip negotiate a compatible set. (Still TODO: a `requirements.lock` for exact reproducibility.)
- **Lesson:** Exact pins work when you control both packages. When packages share a transitive dependency, use ranges and let the resolver work — then lock the result.
