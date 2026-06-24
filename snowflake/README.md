# Snowflake Setup & RBAC

This folder provisions the Snowflake foundation for the OneOnOne analytics pipeline and documents the access-control model. Everything here is version-controlled and reproducible — run one file and the whole warehouse, database, and role structure exists.

## Files

| File | Purpose |
|---|---|
| `setup.sql` | Creates warehouse, database, schemas, roles, and all grants. Heavily commented. |
| `teardown.sql` | Drops everything so you can re-run setup from a clean slate. |
| `run_sql.py` | Executes a `.sql` file from the terminal (one session, so role switches persist). |

## How to run

```bash
source .venv/bin/activate
cd snowflake
python run_sql.py setup.sql      # build it
python run_sql.py teardown.sql   # tear it down (destroys data — reloadable from Supabase)
```

No Snowflake UI required. The `COCOON` user has the admin roles these statements need.

---

## The mental model: how Snowflake RBAC works

Snowflake access control is **role-based**: privileges are never granted to users directly, they're granted to **roles**, and roles are granted to users. A user "becomes" a role to do work.

### Built-in admin roles (separation of concerns)

Snowflake ships with a fixed hierarchy. Each top role owns a different concern — we deliberately use the *right* one for each action instead of doing everything as `ACCOUNTADMIN`:

| Role | Owns / can do | We use it for |
|---|---|---|
| `ACCOUNTADMIN` | Everything (top of tree) | Nothing daily — too powerful |
| `SECURITYADMIN` | Manages grants & role graph | Handing out privileges |
| `USERADMIN` | Creates users & roles | Creating our 3 roles |
| `SYSADMIN` | Owns warehouses, DBs, objects | Creating warehouse, DB, schemas |
| `PUBLIC` | Auto-granted to everyone | Avoid — it's a leak surface |

> **Why not just use ACCOUNTADMIN for everything?** Because then every object is owned at the very top, least privilege is impossible, and one compromised login owns the account. Using the narrowest role that can do the job is the whole point.

### Our functional roles

On top of the built-ins we define **functional roles** — one per pipeline stage. They map to *jobs*, not people:

```
RAW  ───read──►  STAGING ───►  MARTS
 ▲                                │
 │ write                         │ read
 │                                ▼
ONEONONE_LOADER   ONEONONE_TRANSFORMER   ONEONONE_REPORTER
(ingestion)            (dbt)              (agent / BI)
```

| Role | RAW | STAGING | MARTS | Warehouse | Used by |
|---|---|---|---|---|---|
| `ONEONONE_LOADER` | create / write | — | — | USAGE | Python ingestion |
| `ONEONONE_TRANSFORMER` | read | create / write | create / write | USAGE | dbt |
| `ONEONONE_REPORTER` | — | — | read | USAGE | LangGraph agent / BI |

Each row is **least privilege**: the loader can't read your marts, the reporter can't write anything, and only dbt can build the modeled layers.

### Two rules that make it click

1. **Roles roll up to SYSADMIN.** We `GRANT ROLE ONEONONE_* TO ROLE SYSADMIN`. Granting role A to role B makes B *inherit* A — so an admin operating as SYSADMIN automatically has whatever the pipeline roles have. Clean ownership, no separate logins.

2. **FUTURE grants.** `GRANT SELECT ON FUTURE TABLES IN SCHEMA RAW TO ROLE ONEONONE_TRANSFORMER` means tables that **don't exist yet** are automatically readable when created. Without it, every new table the loader creates tomorrow would be invisible to dbt. This is the most commonly forgotten grant.

### Privilege vocabulary (quick reference)

| Privilege | Means |
|---|---|
| `USAGE` on warehouse | May run queries on it (not resize/drop) |
| `USAGE` on DB / schema | May "see into" it (visibility, not data) |
| `SELECT` on table | May read rows |
| `INSERT/UPDATE/DELETE/TRUNCATE` | May change data |
| `CREATE TABLE/VIEW` on schema | May create objects (and owns what it creates) |
| `OWNERSHIP` | Full control incl. drop; auto-held by the creator |

---

## How connections pick a role

A Snowflake connection chooses its role with the `role` parameter. We drive this with the `SNOWFLAKE_ROLE` env var:

- **Ingestion** connects as `ONEONONE_LOADER` (`SNOWFLAKE_ROLE=ONEONONE_LOADER`).
- **dbt** will set `role: ONEONONE_TRANSFORMER` in its `profiles.yml`.
- **The agent** (Week 5) will connect as `ONEONONE_REPORTER`.

Same user, three roles, three levels of access — enforced by Snowflake, not by trust.

## Verify the setup

```sql
SHOW WAREHOUSES LIKE 'ONEONONE_WH';
SHOW SCHEMAS IN DATABASE ONEONONE_DB;
SHOW ROLES LIKE 'ONEONONE_%';
SHOW GRANTS TO ROLE ONEONONE_TRANSFORMER;   -- read the privilege map straight from Snowflake
```
