-- DBA-only, review before applying. Set login authentication separately using a secret store.
-- Run in the approved target database, never via application startup.
BEGIN;
DO $role$
BEGIN
    IF NOT EXISTS (SELECT FROM pg_catalog.pg_roles WHERE rolname = 'chatbot_reader') THEN
        CREATE ROLE chatbot_reader NOLOGIN NOSUPERUSER NOCREATEDB NOCREATEROLE NOINHERIT NOBYPASSRLS;
    END IF;
END
$role$;
ALTER ROLE chatbot_reader SET default_transaction_read_only = on;
ALTER ROLE chatbot_reader SET statement_timeout = '4s';
ALTER ROLE chatbot_reader SET lock_timeout = '1s';
ALTER ROLE chatbot_reader SET idle_in_transaction_session_timeout = '10s';
ALTER ROLE chatbot_reader SET search_path = pg_catalog, chatbot;
REVOKE ALL ON SCHEMA public FROM chatbot_reader;
REVOKE ALL ON ALL TABLES IN SCHEMA public FROM chatbot_reader;
REVOKE ALL ON ALL SEQUENCES IN SCHEMA public FROM chatbot_reader;
REVOKE ALL ON ALL FUNCTIONS IN SCHEMA public FROM chatbot_reader;
GRANT USAGE ON SCHEMA chatbot TO chatbot_reader;
GRANT SELECT ON chatbot.v_tracking, chatbot.v_offices TO chatbot_reader;
COMMIT;
-- Effective PUBLIC grants / role memberships must also be audited by the DBA.
-- Scope GUC is set by trusted backend per transaction; it is NOT an identity mechanism.
-- This role is intentionally global-internal, unsuitable for customers/public clients.
