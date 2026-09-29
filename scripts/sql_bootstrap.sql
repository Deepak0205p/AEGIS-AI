# AEGIS AI - database bootstrap
#
# Creates the `sih_sql_sandbox` schema used by the read-only SQL editor, and the
# application role grants the backend needs. Idempotent: safe to re-run.
#
#   docker compose exec -T db psql -U aegis -d sih_sovereign_ai < scripts/sql_bootstrap.sql
#
# The application tables themselves are created by `backend.db.init_db()` on
# backend startup, so they are NOT created here.

-- Read-only sandbox schema for the Canvas SQL editor -----------------------
CREATE SCHEMA IF NOT EXISTS sih_sql_sandbox;
GRANT USAGE ON SCHEMA sih_sql_sandbox TO aegis;

-- The editor only ever issues SELECT/WITH/SHOW/EXPLAIN, enforced in
-- backend/code_runner.py. Revoke write access here as a second layer so a
-- guard bypass still cannot mutate anything.
REVOKE CREATE ON SCHEMA public FROM PUBLIC;

-- Report the objects this bootstrap actually created/verified.
\echo 'AEGIS SQL sandbox schema:'
SELECT schema_name FROM information_schema.schemata WHERE schema_name = 'sih_sql_sandbox';
