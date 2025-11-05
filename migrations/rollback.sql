-- ============================================================================
-- Discord RAG Bot - Migration Rollback Script
-- ============================================================================
-- Script: rollback.sql
-- Description: Safely rollback database migrations
-- Author: Supabase Schema Architect
-- Date: 2025-11-05
--
-- WARNING: This will delete all data in the new tables!
-- Make sure you have backups before running this script.
--
-- Usage:
--   1. Create backup first: pg_dump -h <host> -U <user> -d <db> > backup.sql
--   2. Run rollback: psql -h <host> -U <user> -d <db> -f rollback.sql
--   3. Verify: SELECT tablename FROM pg_tables WHERE schemaname = 'public';
-- ============================================================================

BEGIN;

-- ============================================================================
-- STEP 1: Backup current data (Optional but recommended)
-- ============================================================================
-- Before dropping tables, you can export data to JSON/CSV:
--
-- COPY (SELECT row_to_json(t) FROM query_history t) TO '/tmp/query_history_backup.json';
-- COPY (SELECT row_to_json(t) FROM user_profiles t) TO '/tmp/user_profiles_backup.json';
-- COPY (SELECT row_to_json(t) FROM feedback t) TO '/tmp/feedback_backup.json';
-- COPY (SELECT row_to_json(t) FROM server_configs t) TO '/tmp/server_configs_backup.json';
--
-- Run these BEFORE the transaction if you want to keep the data

-- ============================================================================
-- STEP 2: Disable RLS (prevent policy errors during drop)
-- ============================================================================

ALTER TABLE IF EXISTS documents DISABLE ROW LEVEL SECURITY;
ALTER TABLE IF EXISTS server_configs DISABLE ROW LEVEL SECURITY;
ALTER TABLE IF EXISTS query_history DISABLE ROW LEVEL SECURITY;
ALTER TABLE IF EXISTS query_cache DISABLE ROW LEVEL SECURITY;
ALTER TABLE IF EXISTS rate_limits DISABLE ROW LEVEL SECURITY;
ALTER TABLE IF EXISTS user_profiles DISABLE ROW LEVEL SECURITY;
ALTER TABLE IF EXISTS feedback DISABLE ROW LEVEL SECURITY;
ALTER TABLE IF EXISTS audit_logs DISABLE ROW LEVEL SECURITY;

-- ============================================================================
-- STEP 3: Drop RLS Policies
-- ============================================================================

-- documents policies
DROP POLICY IF EXISTS documents_service_role_all ON documents;
DROP POLICY IF EXISTS documents_authenticated_read ON documents;
DROP POLICY IF EXISTS documents_anon_read ON documents;

-- server_configs policies
DROP POLICY IF EXISTS server_configs_service_role_all ON server_configs;
DROP POLICY IF EXISTS server_configs_authenticated_read_own ON server_configs;

-- query_history policies
DROP POLICY IF EXISTS query_history_service_role_all ON query_history;
DROP POLICY IF EXISTS query_history_user_read_own ON query_history;

-- query_cache policies
DROP POLICY IF EXISTS query_cache_service_role_all ON query_cache;

-- rate_limits policies
DROP POLICY IF EXISTS rate_limits_service_role_all ON rate_limits;
DROP POLICY IF EXISTS rate_limits_user_read_own ON rate_limits;

-- user_profiles policies
DROP POLICY IF EXISTS user_profiles_service_role_all ON user_profiles;
DROP POLICY IF EXISTS user_profiles_user_read_own ON user_profiles;
DROP POLICY IF EXISTS user_profiles_user_update_own ON user_profiles;

-- feedback policies
DROP POLICY IF EXISTS feedback_service_role_all ON feedback;
DROP POLICY IF EXISTS feedback_user_read_own ON feedback;
DROP POLICY IF EXISTS feedback_user_insert_own ON feedback;

-- audit_logs policies
DROP POLICY IF EXISTS audit_logs_service_role_all ON audit_logs;

-- ============================================================================
-- STEP 4: Drop Helper Functions
-- ============================================================================

DROP FUNCTION IF EXISTS set_user_context(VARCHAR);
DROP FUNCTION IF EXISTS set_guild_context(VARCHAR);
DROP FUNCTION IF EXISTS clear_context();
DROP FUNCTION IF EXISTS update_user_profile(VARCHAR, VARCHAR);
DROP FUNCTION IF EXISTS reset_rate_limit_if_expired(VARCHAR);
DROP FUNCTION IF EXISTS clean_expired_cache();
DROP FUNCTION IF EXISTS match_documents(vector, INT, JSONB);

-- ============================================================================
-- STEP 5: Drop Triggers
-- ============================================================================

DROP TRIGGER IF EXISTS update_documents_updated_at ON documents;
DROP TRIGGER IF EXISTS update_server_configs_updated_at ON server_configs;
DROP FUNCTION IF EXISTS update_updated_at_column();

-- ============================================================================
-- STEP 6: Drop Tables (in reverse dependency order)
-- ============================================================================

-- Drop tables that reference other tables first
DROP TABLE IF EXISTS feedback CASCADE;
DROP TABLE IF EXISTS audit_logs CASCADE;
DROP TABLE IF EXISTS query_history CASCADE;
DROP TABLE IF EXISTS query_cache CASCADE;
DROP TABLE IF EXISTS rate_limits CASCADE;
DROP TABLE IF EXISTS user_profiles CASCADE;
DROP TABLE IF EXISTS server_configs CASCADE;

-- Note: We're keeping the documents table if it existed before
-- If you want to drop it completely, uncomment:
-- DROP TABLE IF EXISTS documents CASCADE;

-- If you want to restore the original simple documents table, uncomment:
/*
DROP TABLE IF EXISTS documents CASCADE;

CREATE TABLE documents (
  id BIGSERIAL PRIMARY KEY,
  content TEXT,
  embedding vector(1536),
  metadata JSONB
);

CREATE INDEX documents_embedding_idx ON documents
  USING ivfflat (embedding vector_cosine_ops)
  WITH (lists = 100);

CREATE OR REPLACE FUNCTION match_documents (
  query_embedding vector(1536),
  match_count int DEFAULT 5,
  filter JSONB DEFAULT '{}'
)
RETURNS TABLE (
  id BIGINT,
  content TEXT,
  metadata JSONB,
  similarity FLOAT
)
LANGUAGE plpgsql
AS $$
BEGIN
  RETURN QUERY
  SELECT
    documents.id,
    documents.content,
    documents.metadata,
    (documents.embedding <=> query_embedding) * -1 AS similarity
  FROM documents
  WHERE (metadata @> filter) OR (filter = '{}')
  ORDER BY documents.embedding <=> query_embedding
  LIMIT match_count;
END;
$$;
*/

-- ============================================================================
-- STEP 7: Drop Extensions (Optional - only if not used elsewhere)
-- ============================================================================
-- Uncomment if you want to remove extensions completely:
-- DROP EXTENSION IF EXISTS pg_trgm;
-- DROP EXTENSION IF EXISTS "uuid-ossp";
-- Note: DO NOT drop vector extension if you're using it for documents table

-- ============================================================================
-- STEP 8: Verification
-- ============================================================================

-- List remaining tables
DO $$
DECLARE
    table_count INTEGER;
BEGIN
    SELECT COUNT(*) INTO table_count
    FROM pg_tables
    WHERE schemaname = 'public'
    AND tablename IN (
        'server_configs', 'query_history', 'query_cache',
        'rate_limits', 'user_profiles', 'feedback', 'audit_logs'
    );

    RAISE NOTICE 'Rollback verification: % tables remaining (should be 0)', table_count;

    IF table_count > 0 THEN
        RAISE WARNING 'Some tables were not dropped. Check for dependencies.';
    ELSE
        RAISE NOTICE 'Rollback successful! All migration tables removed.';
    END IF;
END $$;

COMMIT;

-- ============================================================================
-- Post-Rollback Steps
-- ============================================================================
--
-- 1. If you exported server_config.json data, restore it:
--    - Export from database before rollback:
--      COPY (SELECT guild_id, filter_level, settings FROM server_configs)
--      TO '/tmp/server_configs.csv' WITH CSV HEADER;
--
--    - Convert to server_config.json format manually or with script
--
-- 2. Verify the documents table is intact:
--    SELECT COUNT(*) FROM documents;
--
-- 3. Test the bot functionality:
--    - Run: python bot.py
--    - Test queries
--    - Verify responses work
--
-- 4. If you need to restore data from backup:
--    psql -h <host> -U <user> -d <db> < backup.sql
--
-- ============================================================================
-- Emergency Recovery
-- ============================================================================
-- If rollback fails mid-transaction:
--
-- 1. Check current state:
--    SELECT tablename FROM pg_tables WHERE schemaname = 'public';
--    SELECT proname FROM pg_proc WHERE pronamespace = 'public'::regnamespace;
--
-- 2. Manually drop remaining objects:
--    DROP TABLE IF EXISTS <table_name> CASCADE;
--    DROP FUNCTION IF EXISTS <function_name> CASCADE;
--
-- 3. Restore from backup:
--    psql -h <host> -U <user> -d <db> < backup.sql
--
-- ============================================================================

-- Final confirmation message
SELECT 'Rollback completed. Please verify your database state.' AS status;
