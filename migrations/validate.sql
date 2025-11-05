-- ============================================================================
-- Discord RAG Bot - Migration Validation Script
-- ============================================================================
-- Script: validate.sql
-- Description: Comprehensive validation of schema migration
-- Author: Supabase Schema Architect
-- Date: 2025-11-05
--
-- Usage:
--   psql -h <host> -U <user> -d <db> -f validate.sql
--
-- Expected Output:
--   All checks should return 'PASS' status
--   Any 'FAIL' indicates migration issues that need fixing
-- ============================================================================

\set ON_ERROR_STOP on

BEGIN;

-- ============================================================================
-- Validation Test Suite
-- ============================================================================

-- Create temporary table for test results
CREATE TEMP TABLE validation_results (
    test_category VARCHAR(50),
    test_name VARCHAR(100),
    status VARCHAR(10),
    message TEXT,
    run_at TIMESTAMPTZ DEFAULT NOW()
);

-- ============================================================================
-- TEST 1: Table Existence
-- ============================================================================

DO $$
DECLARE
    expected_tables TEXT[] := ARRAY[
        'documents', 'server_configs', 'query_history', 'query_cache',
        'rate_limits', 'user_profiles', 'feedback', 'audit_logs'
    ];
    table_name TEXT;
    table_exists BOOLEAN;
BEGIN
    FOREACH table_name IN ARRAY expected_tables
    LOOP
        SELECT EXISTS (
            SELECT 1 FROM pg_tables
            WHERE schemaname = 'public' AND tablename = table_name
        ) INTO table_exists;

        IF table_exists THEN
            INSERT INTO validation_results (test_category, test_name, status, message)
            VALUES ('Tables', 'Table: ' || table_name, 'PASS', 'Table exists');
        ELSE
            INSERT INTO validation_results (test_category, test_name, status, message)
            VALUES ('Tables', 'Table: ' || table_name, 'FAIL', 'Table does not exist');
        END IF;
    END LOOP;
END $$;

-- ============================================================================
-- TEST 2: Index Existence
-- ============================================================================

DO $$
DECLARE
    expected_indexes TEXT[] := ARRAY[
        'documents_embedding_idx',
        'documents_document_id_idx',
        'documents_source_name_idx',
        'query_history_user_id_idx',
        'query_history_created_at_idx',
        'query_cache_expires_at_idx',
        'rate_limits_user_id_pkey',
        'user_profiles_pkey'
    ];
    index_name TEXT;
    index_exists BOOLEAN;
BEGIN
    FOREACH index_name IN ARRAY expected_indexes
    LOOP
        SELECT EXISTS (
            SELECT 1 FROM pg_indexes
            WHERE schemaname = 'public' AND indexname = index_name
        ) INTO index_exists;

        IF index_exists THEN
            INSERT INTO validation_results (test_category, test_name, status, message)
            VALUES ('Indexes', 'Index: ' || index_name, 'PASS', 'Index exists');
        ELSE
            INSERT INTO validation_results (test_category, test_name, status, message)
            VALUES ('Indexes', 'Index: ' || index_name, 'FAIL', 'Index does not exist');
        END IF;
    END LOOP;
END $$;

-- ============================================================================
-- TEST 3: Function Existence
-- ============================================================================

DO $$
DECLARE
    expected_functions TEXT[] := ARRAY[
        'match_documents',
        'clean_expired_cache',
        'reset_rate_limit_if_expired',
        'update_user_profile',
        'set_user_context',
        'set_guild_context',
        'clear_context',
        'update_updated_at_column'
    ];
    function_name TEXT;
    function_exists BOOLEAN;
BEGIN
    FOREACH function_name IN ARRAY expected_functions
    LOOP
        SELECT EXISTS (
            SELECT 1 FROM pg_proc
            WHERE proname = function_name
            AND pronamespace = 'public'::regnamespace
        ) INTO function_exists;

        IF function_exists THEN
            INSERT INTO validation_results (test_category, test_name, status, message)
            VALUES ('Functions', 'Function: ' || function_name, 'PASS', 'Function exists');
        ELSE
            INSERT INTO validation_results (test_category, test_name, status, message)
            VALUES ('Functions', 'Function: ' || function_name, 'FAIL', 'Function does not exist');
        END IF;
    END LOOP;
END $$;

-- ============================================================================
-- TEST 4: RLS Enabled
-- ============================================================================

DO $$
DECLARE
    tables_needing_rls TEXT[] := ARRAY[
        'documents', 'server_configs', 'query_history', 'query_cache',
        'rate_limits', 'user_profiles', 'feedback', 'audit_logs'
    ];
    table_name TEXT;
    rls_enabled BOOLEAN;
BEGIN
    FOREACH table_name IN ARRAY tables_needing_rls
    LOOP
        SELECT relrowsecurity INTO rls_enabled
        FROM pg_class
        WHERE relname = table_name AND relnamespace = 'public'::regnamespace;

        IF rls_enabled THEN
            INSERT INTO validation_results (test_category, test_name, status, message)
            VALUES ('RLS', 'RLS: ' || table_name, 'PASS', 'RLS enabled');
        ELSE
            INSERT INTO validation_results (test_category, test_name, status, message)
            VALUES ('RLS', 'RLS: ' || table_name, 'FAIL', 'RLS not enabled');
        END IF;
    END LOOP;
END $$;

-- ============================================================================
-- TEST 5: RLS Policy Existence
-- ============================================================================

DO $$
DECLARE
    policy_count INTEGER;
BEGIN
    SELECT COUNT(*) INTO policy_count
    FROM pg_policies
    WHERE schemaname = 'public';

    IF policy_count >= 15 THEN
        INSERT INTO validation_results (test_category, test_name, status, message)
        VALUES ('RLS', 'Policy Count', 'PASS', policy_count || ' policies found');
    ELSE
        INSERT INTO validation_results (test_category, test_name, status, message)
        VALUES ('RLS', 'Policy Count', 'FAIL', 'Only ' || policy_count || ' policies found, expected >= 15');
    END IF;
END $$;

-- ============================================================================
-- TEST 6: Constraints
-- ============================================================================

DO $$
DECLARE
    constraint_count INTEGER;
BEGIN
    SELECT COUNT(*) INTO constraint_count
    FROM information_schema.table_constraints
    WHERE constraint_schema = 'public'
    AND constraint_type IN ('CHECK', 'FOREIGN KEY', 'PRIMARY KEY', 'UNIQUE');

    IF constraint_count >= 20 THEN
        INSERT INTO validation_results (test_category, test_name, status, message)
        VALUES ('Constraints', 'Constraint Count', 'PASS', constraint_count || ' constraints found');
    ELSE
        INSERT INTO validation_results (test_category, test_name, status, message)
        VALUES ('Constraints', 'Constraint Count', 'FAIL', 'Only ' || constraint_count || ' constraints found');
    END IF;
END $$;

-- ============================================================================
-- TEST 7: Extension Presence
-- ============================================================================

DO $$
DECLARE
    required_extensions TEXT[] := ARRAY['vector', 'uuid-ossp', 'pg_trgm'];
    ext_name TEXT;
    ext_exists BOOLEAN;
BEGIN
    FOREACH ext_name IN ARRAY required_extensions
    LOOP
        SELECT EXISTS (
            SELECT 1 FROM pg_extension WHERE extname = ext_name
        ) INTO ext_exists;

        IF ext_exists THEN
            INSERT INTO validation_results (test_category, test_name, status, message)
            VALUES ('Extensions', 'Extension: ' || ext_name, 'PASS', 'Extension installed');
        ELSE
            INSERT INTO validation_results (test_category, test_name, status, message)
            VALUES ('Extensions', 'Extension: ' || ext_name, 'FAIL', 'Extension not installed');
        END IF;
    END LOOP;
END $$;

-- ============================================================================
-- TEST 8: Column Data Types
-- ============================================================================

DO $$
BEGIN
    -- Check vector dimension in documents table
    IF EXISTS (
        SELECT 1 FROM information_schema.columns
        WHERE table_name = 'documents'
        AND column_name = 'embedding'
        AND udt_name = 'vector'
    ) THEN
        INSERT INTO validation_results (test_category, test_name, status, message)
        VALUES ('Data Types', 'documents.embedding vector type', 'PASS', 'Correct data type');
    ELSE
        INSERT INTO validation_results (test_category, test_name, status, message)
        VALUES ('Data Types', 'documents.embedding vector type', 'FAIL', 'Incorrect data type');
    END IF;

    -- Check JSONB columns
    IF (SELECT COUNT(*) FROM information_schema.columns
        WHERE table_schema = 'public'
        AND data_type = 'jsonb') >= 8 THEN
        INSERT INTO validation_results (test_category, test_name, status, message)
        VALUES ('Data Types', 'JSONB columns', 'PASS', 'JSONB columns present');
    ELSE
        INSERT INTO validation_results (test_category, test_name, status, message)
        VALUES ('Data Types', 'JSONB columns', 'FAIL', 'Missing JSONB columns');
    END IF;
END $$;

-- ============================================================================
-- TEST 9: Trigger Existence
-- ============================================================================

DO $$
DECLARE
    trigger_count INTEGER;
BEGIN
    SELECT COUNT(*) INTO trigger_count
    FROM information_schema.triggers
    WHERE trigger_schema = 'public'
    AND trigger_name LIKE 'update_%_updated_at';

    IF trigger_count >= 2 THEN
        INSERT INTO validation_results (test_category, test_name, status, message)
        VALUES ('Triggers', 'Update Triggers', 'PASS', trigger_count || ' triggers found');
    ELSE
        INSERT INTO validation_results (test_category, test_name, status, message)
        VALUES ('Triggers', 'Update Triggers', 'FAIL', 'Only ' || trigger_count || ' triggers found');
    END IF;
END $$;

-- ============================================================================
-- TEST 10: Sample Data Insertion (Dry Run)
-- ============================================================================

DO $$
BEGIN
    -- Test inserting into server_configs
    BEGIN
        INSERT INTO server_configs (guild_id, filter_level)
        VALUES ('test_guild_123', 'moderado');

        DELETE FROM server_configs WHERE guild_id = 'test_guild_123';

        INSERT INTO validation_results (test_category, test_name, status, message)
        VALUES ('Data Operations', 'INSERT server_configs', 'PASS', 'Can insert and delete');
    EXCEPTION WHEN OTHERS THEN
        INSERT INTO validation_results (test_category, test_name, status, message)
        VALUES ('Data Operations', 'INSERT server_configs', 'FAIL', SQLERRM);
    END;

    -- Test inserting into user_profiles
    BEGIN
        INSERT INTO user_profiles (user_id, total_queries)
        VALUES ('test_user_123', 1);

        DELETE FROM user_profiles WHERE user_id = 'test_user_123';

        INSERT INTO validation_results (test_category, test_name, status, message)
        VALUES ('Data Operations', 'INSERT user_profiles', 'PASS', 'Can insert and delete');
    EXCEPTION WHEN OTHERS THEN
        INSERT INTO validation_results (test_category, test_name, status, message)
        VALUES ('Data Operations', 'INSERT user_profiles', 'FAIL', SQLERRM);
    END;
END $$;

-- ============================================================================
-- TEST 11: Performance Check
-- ============================================================================

DO $$
DECLARE
    start_time TIMESTAMPTZ;
    end_time TIMESTAMPTZ;
    duration_ms NUMERIC;
BEGIN
    -- Test query performance on documents table
    start_time := clock_timestamp();

    PERFORM COUNT(*) FROM documents;

    end_time := clock_timestamp();
    duration_ms := EXTRACT(MILLISECONDS FROM (end_time - start_time));

    IF duration_ms < 100 THEN
        INSERT INTO validation_results (test_category, test_name, status, message)
        VALUES ('Performance', 'documents COUNT query', 'PASS', duration_ms || 'ms');
    ELSE
        INSERT INTO validation_results (test_category, test_name, status, message)
        VALUES ('Performance', 'documents COUNT query', 'WARN', duration_ms || 'ms (slow)');
    END IF;
END $$;

-- ============================================================================
-- Display Results
-- ============================================================================

-- Summary by category
SELECT
    test_category,
    COUNT(*) AS total_tests,
    SUM(CASE WHEN status = 'PASS' THEN 1 ELSE 0 END) AS passed,
    SUM(CASE WHEN status = 'FAIL' THEN 1 ELSE 0 END) AS failed,
    SUM(CASE WHEN status = 'WARN' THEN 1 ELSE 0 END) AS warnings
FROM validation_results
GROUP BY test_category
ORDER BY test_category;

-- Detailed results
SELECT
    test_category,
    test_name,
    status,
    message
FROM validation_results
ORDER BY
    CASE status
        WHEN 'FAIL' THEN 1
        WHEN 'WARN' THEN 2
        WHEN 'PASS' THEN 3
    END,
    test_category,
    test_name;

-- Overall summary
DO $$
DECLARE
    total_tests INTEGER;
    passed_tests INTEGER;
    failed_tests INTEGER;
BEGIN
    SELECT COUNT(*), SUM(CASE WHEN status = 'PASS' THEN 1 ELSE 0 END), SUM(CASE WHEN status = 'FAIL' THEN 1 ELSE 0 END)
    INTO total_tests, passed_tests, failed_tests
    FROM validation_results;

    RAISE NOTICE '';
    RAISE NOTICE '============================================================';
    RAISE NOTICE 'VALIDATION SUMMARY';
    RAISE NOTICE '============================================================';
    RAISE NOTICE 'Total Tests: %', total_tests;
    RAISE NOTICE 'Passed: %', passed_tests;
    RAISE NOTICE 'Failed: %', failed_tests;
    RAISE NOTICE 'Success Rate: %% ', ROUND((passed_tests::NUMERIC / total_tests * 100), 2);
    RAISE NOTICE '============================================================';

    IF failed_tests = 0 THEN
        RAISE NOTICE '✓ All validation tests passed!';
        RAISE NOTICE 'Migration is successful and ready for production.';
    ELSE
        RAISE NOTICE '✗ Some tests failed. Please review and fix issues.';
    END IF;
    RAISE NOTICE '';
END $$;

COMMIT;

-- ============================================================================
-- Additional Manual Checks
-- ============================================================================
-- After running this script, manually verify:
--
-- 1. Check table sizes:
--    SELECT schemaname, tablename, pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename))
--    FROM pg_tables WHERE schemaname = 'public' ORDER BY pg_total_relation_size(schemaname||'.'||tablename) DESC;
--
-- 2. Check index usage:
--    SELECT schemaname, tablename, indexname, idx_scan, idx_tup_read, idx_tup_fetch
--    FROM pg_stat_user_indexes WHERE schemaname = 'public' ORDER BY idx_scan DESC;
--
-- 3. Test vector search:
--    SELECT * FROM match_documents(
--        (SELECT embedding FROM documents LIMIT 1)::vector(1536),
--        5
--    );
--
-- 4. Test RLS policies with different roles:
--    SET ROLE service_role; SELECT COUNT(*) FROM query_history; RESET ROLE;
--    SET ROLE authenticated; SELECT set_user_context('123'); SELECT COUNT(*) FROM query_history; RESET ROLE;
--
-- ============================================================================
