-- ============================================================================
-- OneOnOne Analytics — Snowflake foundation setup
-- ============================================================================
-- Run this as a user that has ACCOUNTADMIN available (COCOON does).
-- It creates: 1 warehouse, 1 database, 3 schemas, 3 functional roles,
-- and the least-privilege grants that wire them together.
--
-- WHY THIS ORDER: in Snowflake, different built-in admin roles own different
-- concerns. We deliberately switch roles as we go so each object is created by
-- the role that *should* own it. This is the single most important habit in
-- Snowflake RBAC.
--
--   SYSADMIN       -> owns compute + data objects (warehouses, DBs, schemas)
--   USERADMIN      -> creates roles and users
--   SECURITYADMIN  -> manages grants and the role hierarchy
--   ACCOUNTADMIN   -> top of the tree; we avoid using it for daily work
-- ============================================================================


-- ----------------------------------------------------------------------------
-- STEP 1 — Compute + data objects (owned by SYSADMIN)
-- ----------------------------------------------------------------------------
-- SYSADMIN is the conventional owner of all warehouses and databases. If we
-- created these as ACCOUNTADMIN, ownership would sit at the very top and every
-- other role would need explicit grants just to function. Owning at SYSADMIN
-- keeps the hierarchy clean.
USE ROLE SYSADMIN;

-- A warehouse is Snowflake's COMPUTE. It is separate from storage. Queries cost
-- money only while a warehouse is running, so we keep it small and let it
-- auto-suspend when idle.
CREATE WAREHOUSE IF NOT EXISTS ONEONONE_WH
    WAREHOUSE_SIZE       = 'XSMALL'   -- smallest/cheapest; plenty for our data volume
    AUTO_SUSPEND         = 60         -- seconds of idle before it powers down (stops billing)
    AUTO_RESUME          = TRUE       -- powers back on automatically when a query arrives
    INITIALLY_SUSPENDED  = TRUE       -- don't start (and bill) the moment it's created
    COMMENT              = 'Compute for the OneOnOne analytics pipeline';

-- A database is a logical container. Inside it we use one SCHEMA per pipeline
-- LAYER — this is the standard analytics-engineering layout. Data flows left to
-- right: RAW (landing) -> STAGING (cleaned) -> INTERMEDIATE (reusable glue) -> MARTS.
CREATE DATABASE IF NOT EXISTS ONEONONE_DB
    COMMENT = 'OneOnOne analytics warehouse';

USE DATABASE ONEONONE_DB;

CREATE SCHEMA IF NOT EXISTS RAW
    COMMENT = 'Landing zone. Python ingestion writes here. All columns VARCHAR, untyped.';
CREATE SCHEMA IF NOT EXISTS STAGING
    COMMENT = 'dbt staging models (views). Typed, renamed, snake_case. No business logic.';
CREATE SCHEMA IF NOT EXISTS INTERMEDIATE
    COMMENT = 'dbt intermediate models (views). Reusable joins/derivations shared across marts.';
CREATE SCHEMA IF NOT EXISTS MARTS
    COMMENT = 'dbt marts (tables). Business logic: dims, facts, health marts.';
CREATE SCHEMA IF NOT EXISTS SNAPSHOTS
    COMMENT = 'dbt SCD Type 2 snapshots. Historical record of source-record changes.';


-- ----------------------------------------------------------------------------
-- STEP 2 — Create the functional roles (owned by USERADMIN)
-- ----------------------------------------------------------------------------
-- A "functional role" maps to a JOB someone/something does, not to a person.
-- We define three, one per stage of the pipeline. Naming is project-prefixed
-- (ONEONONE_*) so that if this account ever hosts another project, role names
-- never collide and ownership is obvious.
USE ROLE USERADMIN;

CREATE ROLE IF NOT EXISTS ONEONONE_LOADER
    COMMENT = 'Ingestion. Writes raw data into ONEONONE_DB.RAW only.';
CREATE ROLE IF NOT EXISTS ONEONONE_TRANSFORMER
    COMMENT = 'dbt. Reads RAW, builds STAGING and MARTS.';
CREATE ROLE IF NOT EXISTS ONEONONE_REPORTER
    COMMENT = 'Read-only consumer of MARTS (LangGraph agent / BI).';


-- ----------------------------------------------------------------------------
-- STEP 3 — Grants (managed by SECURITYADMIN)
-- ----------------------------------------------------------------------------
-- SECURITYADMIN holds the global MANAGE GRANTS privilege, so it is the correct
-- role for handing out access. Everything below follows LEAST PRIVILEGE: each
-- role gets exactly what its job needs and nothing more.
USE ROLE SECURITYADMIN;

-- 3a. Role hierarchy: roll the functional roles up into SYSADMIN.
-- WHY: in Snowflake, granting role A to role B means B INHERITS A's privileges.
-- By granting our roles to SYSADMIN, any admin operating as SYSADMIN can see and
-- manage everything the pipeline can touch — without us logging in as each role.
GRANT ROLE ONEONONE_LOADER      TO ROLE SYSADMIN;
GRANT ROLE ONEONONE_TRANSFORMER TO ROLE SYSADMIN;
GRANT ROLE ONEONONE_REPORTER    TO ROLE SYSADMIN;

-- 3b. Warehouse usage: a role can't run a query without USAGE on a warehouse.
-- All three need compute. (USAGE = "may use it", not "may resize/drop it".)
GRANT USAGE ON WAREHOUSE ONEONONE_WH TO ROLE ONEONONE_LOADER;
GRANT USAGE ON WAREHOUSE ONEONONE_WH TO ROLE ONEONONE_TRANSFORMER;
GRANT USAGE ON WAREHOUSE ONEONONE_WH TO ROLE ONEONONE_REPORTER;

-- 3c. Database usage: a role must be able to "see" the database before it can
-- touch anything inside it. USAGE on a DB/schema = visibility, not data access.
GRANT USAGE ON DATABASE ONEONONE_DB TO ROLE ONEONONE_LOADER;
GRANT USAGE ON DATABASE ONEONONE_DB TO ROLE ONEONONE_TRANSFORMER;
GRANT USAGE ON DATABASE ONEONONE_DB TO ROLE ONEONONE_REPORTER;

-- 3d. LOADER — full control of RAW, nothing else.
-- The ingestion script DROPs and reCREATEs each table every run. To do that the
-- role needs CREATE TABLE on the schema; whoever creates a table OWNS it and can
-- therefore drop it. So CREATE TABLE alone covers the drop+recreate+insert cycle.
GRANT USAGE ON SCHEMA ONEONONE_DB.RAW TO ROLE ONEONONE_LOADER;
GRANT CREATE TABLE ON SCHEMA ONEONONE_DB.RAW TO ROLE ONEONONE_LOADER;
-- Also allow DML on any tables that already exist (e.g. created by a prior run
-- under a different role) so LOADER is never blocked mid-pipeline.
GRANT SELECT, INSERT, UPDATE, DELETE, TRUNCATE
    ON ALL TABLES IN SCHEMA ONEONONE_DB.RAW TO ROLE ONEONONE_LOADER;
GRANT SELECT, INSERT, UPDATE, DELETE, TRUNCATE
    ON FUTURE TABLES IN SCHEMA ONEONONE_DB.RAW TO ROLE ONEONONE_LOADER;

-- 3e. TRANSFORMER — READ raw, BUILD staging + marts.
-- This is dbt's role. It reads the landing zone and writes the modeled layers.
GRANT USAGE ON SCHEMA ONEONONE_DB.RAW TO ROLE ONEONONE_TRANSFORMER;
GRANT SELECT ON ALL TABLES    IN SCHEMA ONEONONE_DB.RAW TO ROLE ONEONONE_TRANSFORMER;
-- FUTURE TABLES is the critical line: without it, any table the LOADER creates
-- *tomorrow* would be invisible to dbt. FUTURE grants apply automatically to
-- objects that don't exist yet. This is the #1 thing people forget.
GRANT SELECT ON FUTURE TABLES IN SCHEMA ONEONONE_DB.RAW TO ROLE ONEONONE_TRANSFORMER;

-- dbt needs to create both views (staging/intermediate) and tables (marts) here.
GRANT USAGE, CREATE TABLE, CREATE VIEW
    ON SCHEMA ONEONONE_DB.STAGING      TO ROLE ONEONONE_TRANSFORMER;
GRANT USAGE, CREATE TABLE, CREATE VIEW
    ON SCHEMA ONEONONE_DB.INTERMEDIATE TO ROLE ONEONONE_TRANSFORMER;
GRANT USAGE, CREATE TABLE, CREATE VIEW
    ON SCHEMA ONEONONE_DB.MARTS        TO ROLE ONEONONE_TRANSFORMER;
GRANT USAGE, CREATE TABLE, CREATE VIEW
    ON SCHEMA ONEONONE_DB.SNAPSHOTS    TO ROLE ONEONONE_TRANSFORMER;

-- 3f. REPORTER — read-only on MARTS and SNAPSHOTS (the curated end product).
-- The AI analyst and any BI tool query here. They can never see RAW or STAGING,
-- and can never write anything. This is least privilege at its strictest.
GRANT USAGE ON SCHEMA ONEONONE_DB.MARTS TO ROLE ONEONONE_REPORTER;
GRANT SELECT ON ALL TABLES    IN SCHEMA ONEONONE_DB.MARTS TO ROLE ONEONONE_REPORTER;
GRANT SELECT ON FUTURE TABLES IN SCHEMA ONEONONE_DB.MARTS TO ROLE ONEONONE_REPORTER;
GRANT SELECT ON ALL VIEWS     IN SCHEMA ONEONONE_DB.MARTS TO ROLE ONEONONE_REPORTER;
GRANT SELECT ON FUTURE VIEWS  IN SCHEMA ONEONONE_DB.MARTS TO ROLE ONEONONE_REPORTER;
GRANT USAGE ON SCHEMA ONEONONE_DB.SNAPSHOTS TO ROLE ONEONONE_REPORTER;
GRANT SELECT ON ALL TABLES    IN SCHEMA ONEONONE_DB.SNAPSHOTS TO ROLE ONEONONE_REPORTER;
GRANT SELECT ON FUTURE TABLES IN SCHEMA ONEONONE_DB.SNAPSHOTS TO ROLE ONEONONE_REPORTER;


-- ----------------------------------------------------------------------------
-- STEP 4 — Attach the roles to a human (the COCOON user)
-- ----------------------------------------------------------------------------
-- Roles do nothing until granted to a user. For now we grant all three to your
-- existing COCOON user; you "become" a role per connection via the role param.
-- (Later, before the GitHub Actions cron, the LOADER role should move to a
--  dedicated service user so CI never holds your admin credentials.)
GRANT ROLE ONEONONE_LOADER      TO USER COCOON;
GRANT ROLE ONEONONE_TRANSFORMER TO USER COCOON;
GRANT ROLE ONEONONE_REPORTER    TO USER COCOON;
