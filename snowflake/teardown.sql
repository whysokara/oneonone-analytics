-- ============================================================================
-- OneOnOne Analytics — teardown
-- ============================================================================
-- Drops everything setup.sql created so you can re-run from a clean slate while
-- learning. Order is the reverse of creation: drop the things that depend on
-- others first. DROP ... IF EXISTS makes this safe to run repeatedly.
--
-- WARNING: dropping ONEONONE_DB destroys all ingested data. That's fine here —
-- the ingestion script can reload it from Supabase in seconds.
-- ============================================================================

-- Roles are dropped by USERADMIN (the role that created them).
USE ROLE USERADMIN;
DROP ROLE IF EXISTS ONEONONE_LOADER;
DROP ROLE IF EXISTS ONEONONE_TRANSFORMER;
DROP ROLE IF EXISTS ONEONONE_REPORTER;

-- Database and warehouse are dropped by their owner, SYSADMIN.
USE ROLE SYSADMIN;
DROP DATABASE  IF EXISTS ONEONONE_DB;   -- cascades to RAW/STAGING/MARTS and all tables
DROP WAREHOUSE IF EXISTS ONEONONE_WH;
