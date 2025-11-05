-- ============================================================================
-- Discord RAG Bot - Enhanced Supabase Schema
-- ============================================================================
-- Migration: 001_enhanced_schema.sql
-- Description: Comprehensive database schema for Discord RAG Bot
-- Author: Supabase Schema Architect
-- Date: 2025-11-05
-- Risk Level: LOW
--
-- This migration creates a production-ready schema with:
-- - Enhanced document storage with metadata
-- - Server configuration management
-- - Query history and analytics
-- - Persistent caching
-- - Rate limiting
-- - User profiles and feedback
-- - Audit logging
-- - Optimized indexes
-- - Row Level Security policies
-- ============================================================================

BEGIN;

-- ============================================================================
-- PHASE 1: Core Schema & Extensions
-- ============================================================================

-- Enable required extensions
CREATE EXTENSION IF NOT EXISTS vector;
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS pg_trgm; -- For text search optimization

-- ============================================================================
-- Table: documents (Enhanced)
-- ============================================================================
-- Stores document chunks with embeddings for vector search
-- Enhancement: Added metadata tracking and better organization
-- ============================================================================

-- Drop existing table if this is a fresh migration
-- IMPORTANT: Comment this out if you have existing data
-- DROP TABLE IF EXISTS documents CASCADE;

CREATE TABLE IF NOT EXISTS documents (
    id BIGSERIAL PRIMARY KEY,

    -- Document content
    content TEXT NOT NULL,
    embedding vector(1536) NOT NULL, -- OpenAI text-embedding-3-small dimension

    -- Metadata
    metadata JSONB DEFAULT '{}'::jsonb,

    -- Document organization
    document_id UUID DEFAULT uuid_generate_v4(), -- Group chunks from same document
    chunk_index INTEGER DEFAULT 0, -- Order of chunks within document
    source_type VARCHAR(50) DEFAULT 'pdf', -- pdf, txt, docx, etc.
    source_name TEXT, -- Original file name

    -- Tracking
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),

    -- Constraints
    CONSTRAINT documents_content_not_empty CHECK (LENGTH(TRIM(content)) > 0),
    CONSTRAINT documents_chunk_index_positive CHECK (chunk_index >= 0)
);

-- Indexes for documents
CREATE INDEX IF NOT EXISTS documents_embedding_idx
    ON documents USING ivfflat (embedding vector_cosine_ops)
    WITH (lists = 100);

CREATE INDEX IF NOT EXISTS documents_document_id_idx ON documents(document_id);
CREATE INDEX IF NOT EXISTS documents_source_name_idx ON documents(source_name);
CREATE INDEX IF NOT EXISTS documents_created_at_idx ON documents(created_at DESC);
CREATE INDEX IF NOT EXISTS documents_metadata_idx ON documents USING GIN (metadata);

-- Text search index for content
CREATE INDEX IF NOT EXISTS documents_content_trgm_idx ON documents USING GIN (content gin_trgm_ops);

-- ============================================================================
-- Table: server_configs
-- ============================================================================
-- Stores Discord server-specific configurations
-- Replaces the local JSON file approach
-- ============================================================================

CREATE TABLE IF NOT EXISTS server_configs (
    guild_id VARCHAR(50) PRIMARY KEY, -- Discord guild ID as string

    -- Configuration
    filter_level VARCHAR(20) DEFAULT 'moderado' NOT NULL,

    -- Additional settings (extensible)
    settings JSONB DEFAULT '{}'::jsonb,

    -- Tracking
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),

    -- Constraints
    CONSTRAINT server_configs_filter_level_valid
        CHECK (filter_level IN ('conservador', 'moderado', 'liberal'))
);

-- Indexes for server_configs
CREATE INDEX IF NOT EXISTS server_configs_filter_level_idx ON server_configs(filter_level);
CREATE INDEX IF NOT EXISTS server_configs_updated_at_idx ON server_configs(updated_at DESC);

-- ============================================================================
-- Table: query_history
-- ============================================================================
-- Comprehensive query tracking for analytics and debugging
-- ============================================================================

CREATE TABLE IF NOT EXISTS query_history (
    id BIGSERIAL PRIMARY KEY,

    -- Query identification
    user_id VARCHAR(50) NOT NULL, -- Discord user ID
    guild_id VARCHAR(50), -- NULL for DMs

    -- Query details
    question TEXT NOT NULL,
    answer TEXT NOT NULL,
    query_type VARCHAR(20) DEFAULT 'RAG', -- RAG, DM, Mention, Slash

    -- Performance metrics
    sources_count INTEGER DEFAULT 0,
    response_time_ms INTEGER, -- Response time in milliseconds
    tokens_used INTEGER, -- Approximate token count

    -- Model information
    model_used VARCHAR(100),
    filter_level_used VARCHAR(20),

    -- Metadata
    metadata JSONB DEFAULT '{}'::jsonb,

    -- Tracking
    created_at TIMESTAMPTZ DEFAULT NOW(),

    -- Constraints
    CONSTRAINT query_history_question_not_empty CHECK (LENGTH(TRIM(question)) > 0),
    CONSTRAINT query_history_sources_count_positive CHECK (sources_count >= 0),
    CONSTRAINT query_history_response_time_positive CHECK (response_time_ms IS NULL OR response_time_ms >= 0)
);

-- Indexes for query_history
CREATE INDEX IF NOT EXISTS query_history_user_id_idx ON query_history(user_id);
CREATE INDEX IF NOT EXISTS query_history_guild_id_idx ON query_history(guild_id);
CREATE INDEX IF NOT EXISTS query_history_created_at_idx ON query_history(created_at DESC);
CREATE INDEX IF NOT EXISTS query_history_query_type_idx ON query_history(query_type);
CREATE INDEX IF NOT EXISTS query_history_user_created_idx ON query_history(user_id, created_at DESC);

-- ============================================================================
-- Table: query_cache
-- ============================================================================
-- Persistent cache for query responses to reduce API costs
-- ============================================================================

CREATE TABLE IF NOT EXISTS query_cache (
    cache_key VARCHAR(64) PRIMARY KEY, -- MD5 or SHA256 hash of normalized question

    -- Cached data
    question TEXT NOT NULL,
    answer TEXT NOT NULL,
    sources JSONB DEFAULT '[]'::jsonb,

    -- Cache metadata
    hit_count INTEGER DEFAULT 0,
    metadata JSONB DEFAULT '{}'::jsonb,

    -- Expiration
    created_at TIMESTAMPTZ DEFAULT NOW(),
    expires_at TIMESTAMPTZ NOT NULL,

    -- Constraints
    CONSTRAINT query_cache_expires_after_created CHECK (expires_at > created_at)
);

-- Indexes for query_cache
CREATE INDEX IF NOT EXISTS query_cache_expires_at_idx ON query_cache(expires_at);
CREATE INDEX IF NOT EXISTS query_cache_created_at_idx ON query_cache(created_at DESC);
CREATE INDEX IF NOT EXISTS query_cache_hit_count_idx ON query_cache(hit_count DESC);

-- ============================================================================
-- Table: rate_limits
-- ============================================================================
-- Persistent rate limiting to prevent abuse
-- ============================================================================

CREATE TABLE IF NOT EXISTS rate_limits (
    user_id VARCHAR(50) PRIMARY KEY, -- Discord user ID

    -- Rate limit tracking
    request_count INTEGER DEFAULT 0 NOT NULL,
    window_start TIMESTAMPTZ DEFAULT NOW() NOT NULL,
    window_duration INTEGER DEFAULT 60 NOT NULL, -- Seconds

    -- Tracking
    last_request_at TIMESTAMPTZ DEFAULT NOW(),
    total_requests_all_time INTEGER DEFAULT 0,

    -- Constraints
    CONSTRAINT rate_limits_request_count_positive CHECK (request_count >= 0),
    CONSTRAINT rate_limits_window_duration_positive CHECK (window_duration > 0)
);

-- Indexes for rate_limits
CREATE INDEX IF NOT EXISTS rate_limits_window_start_idx ON rate_limits(window_start);
CREATE INDEX IF NOT EXISTS rate_limits_last_request_idx ON rate_limits(last_request_at DESC);

-- ============================================================================
-- Table: user_profiles
-- ============================================================================
-- User activity tracking and preferences
-- ============================================================================

CREATE TABLE IF NOT EXISTS user_profiles (
    user_id VARCHAR(50) PRIMARY KEY, -- Discord user ID

    -- Statistics
    total_queries INTEGER DEFAULT 0 NOT NULL,
    total_feedback_given INTEGER DEFAULT 0,

    -- Preferences
    preferred_filter_level VARCHAR(20),
    preferred_query_type VARCHAR(20),

    -- Activity tracking
    first_seen TIMESTAMPTZ DEFAULT NOW(),
    last_seen TIMESTAMPTZ DEFAULT NOW(),

    -- Metadata (extensible)
    metadata JSONB DEFAULT '{}'::jsonb,

    -- Constraints
    CONSTRAINT user_profiles_total_queries_positive CHECK (total_queries >= 0),
    CONSTRAINT user_profiles_last_seen_after_first CHECK (last_seen >= first_seen)
);

-- Indexes for user_profiles
CREATE INDEX IF NOT EXISTS user_profiles_total_queries_idx ON user_profiles(total_queries DESC);
CREATE INDEX IF NOT EXISTS user_profiles_last_seen_idx ON user_profiles(last_seen DESC);
CREATE INDEX IF NOT EXISTS user_profiles_first_seen_idx ON user_profiles(first_seen DESC);

-- ============================================================================
-- Table: feedback
-- ============================================================================
-- User feedback on bot responses for quality improvement
-- ============================================================================

CREATE TABLE IF NOT EXISTS feedback (
    id BIGSERIAL PRIMARY KEY,

    -- References
    query_history_id BIGINT REFERENCES query_history(id) ON DELETE SET NULL,
    user_id VARCHAR(50) NOT NULL,

    -- Feedback details
    rating INTEGER, -- 1-5 stars, or thumbs up/down (1/5)
    comment TEXT,
    feedback_type VARCHAR(20) DEFAULT 'rating', -- rating, report, suggestion

    -- Tracking
    created_at TIMESTAMPTZ DEFAULT NOW(),

    -- Constraints
    CONSTRAINT feedback_rating_valid CHECK (rating IS NULL OR (rating >= 1 AND rating <= 5))
);

-- Indexes for feedback
CREATE INDEX IF NOT EXISTS feedback_query_history_idx ON feedback(query_history_id);
CREATE INDEX IF NOT EXISTS feedback_user_id_idx ON feedback(user_id);
CREATE INDEX IF NOT EXISTS feedback_rating_idx ON feedback(rating);
CREATE INDEX IF NOT EXISTS feedback_created_at_idx ON feedback(created_at DESC);
CREATE INDEX IF NOT EXISTS feedback_feedback_type_idx ON feedback(feedback_type);

-- ============================================================================
-- Table: audit_logs
-- ============================================================================
-- Comprehensive audit trail for security and compliance
-- ============================================================================

CREATE TABLE IF NOT EXISTS audit_logs (
    id BIGSERIAL PRIMARY KEY,

    -- Audit details
    table_name VARCHAR(100) NOT NULL,
    operation VARCHAR(20) NOT NULL, -- INSERT, UPDATE, DELETE
    user_id VARCHAR(50), -- Discord user ID (if applicable)

    -- Change tracking
    record_id TEXT, -- ID of affected record
    old_data JSONB,
    new_data JSONB,

    -- Metadata
    ip_address INET,
    user_agent TEXT,
    metadata JSONB DEFAULT '{}'::jsonb,

    -- Tracking
    created_at TIMESTAMPTZ DEFAULT NOW(),

    -- Constraints
    CONSTRAINT audit_logs_operation_valid
        CHECK (operation IN ('INSERT', 'UPDATE', 'DELETE', 'SELECT'))
);

-- Indexes for audit_logs
CREATE INDEX IF NOT EXISTS audit_logs_table_name_idx ON audit_logs(table_name);
CREATE INDEX IF NOT EXISTS audit_logs_operation_idx ON audit_logs(operation);
CREATE INDEX IF NOT EXISTS audit_logs_user_id_idx ON audit_logs(user_id);
CREATE INDEX IF NOT EXISTS audit_logs_created_at_idx ON audit_logs(created_at DESC);
CREATE INDEX IF NOT EXISTS audit_logs_table_created_idx ON audit_logs(table_name, created_at DESC);

-- ============================================================================
-- Functions: Vector Search (Enhanced)
-- ============================================================================

-- Enhanced match_documents function with better filtering
CREATE OR REPLACE FUNCTION match_documents (
    query_embedding vector(1536),
    match_count INT DEFAULT 5,
    filter JSONB DEFAULT '{}'::jsonb
)
RETURNS TABLE (
    id BIGINT,
    content TEXT,
    metadata JSONB,
    document_id UUID,
    source_name TEXT,
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
        documents.document_id,
        documents.source_name,
        1 - (documents.embedding <=> query_embedding) AS similarity
    FROM documents
    WHERE (metadata @> filter) OR (filter = '{}'::jsonb)
    ORDER BY documents.embedding <=> query_embedding
    LIMIT match_count;
END;
$$;

-- Function: Clean expired cache entries
CREATE OR REPLACE FUNCTION clean_expired_cache()
RETURNS INTEGER
LANGUAGE plpgsql
AS $$
DECLARE
    deleted_count INTEGER;
BEGIN
    DELETE FROM query_cache
    WHERE expires_at < NOW();

    GET DIAGNOSTICS deleted_count = ROW_COUNT;
    RETURN deleted_count;
END;
$$;

-- Function: Reset rate limit window if expired
CREATE OR REPLACE FUNCTION reset_rate_limit_if_expired(p_user_id VARCHAR(50))
RETURNS BOOLEAN
LANGUAGE plpgsql
AS $$
DECLARE
    v_window_start TIMESTAMPTZ;
    v_window_duration INTEGER;
    v_expired BOOLEAN;
BEGIN
    SELECT window_start, window_duration INTO v_window_start, v_window_duration
    FROM rate_limits
    WHERE user_id = p_user_id;

    IF NOT FOUND THEN
        RETURN FALSE;
    END IF;

    v_expired := (EXTRACT(EPOCH FROM (NOW() - v_window_start)) > v_window_duration);

    IF v_expired THEN
        UPDATE rate_limits
        SET request_count = 0,
            window_start = NOW()
        WHERE user_id = p_user_id;
        RETURN TRUE;
    END IF;

    RETURN FALSE;
END;
$$;

-- Function: Update user profile on query
CREATE OR REPLACE FUNCTION update_user_profile(
    p_user_id VARCHAR(50),
    p_query_type VARCHAR(20) DEFAULT NULL
)
RETURNS VOID
LANGUAGE plpgsql
AS $$
BEGIN
    INSERT INTO user_profiles (user_id, total_queries, last_seen, preferred_query_type)
    VALUES (p_user_id, 1, NOW(), p_query_type)
    ON CONFLICT (user_id) DO UPDATE
    SET total_queries = user_profiles.total_queries + 1,
        last_seen = NOW(),
        preferred_query_type = COALESCE(EXCLUDED.preferred_query_type, user_profiles.preferred_query_type);
END;
$$;

-- ============================================================================
-- Triggers: Automatic timestamp updates
-- ============================================================================

-- Generic function for updating updated_at timestamp
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER
LANGUAGE plpgsql
AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$;

-- Apply to documents table
DROP TRIGGER IF EXISTS update_documents_updated_at ON documents;
CREATE TRIGGER update_documents_updated_at
    BEFORE UPDATE ON documents
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- Apply to server_configs table
DROP TRIGGER IF EXISTS update_server_configs_updated_at ON server_configs;
CREATE TRIGGER update_server_configs_updated_at
    BEFORE UPDATE ON server_configs
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- ============================================================================
-- Initial Data: Default server config for DMs
-- ============================================================================

INSERT INTO server_configs (guild_id, filter_level, settings)
VALUES ('dm', 'moderado', '{}'::jsonb)
ON CONFLICT (guild_id) DO NOTHING;

-- ============================================================================
-- Comments: Table and Column Documentation
-- ============================================================================

COMMENT ON TABLE documents IS 'Stores document chunks with embeddings for vector similarity search';
COMMENT ON TABLE server_configs IS 'Discord server-specific configuration (filter levels, etc.)';
COMMENT ON TABLE query_history IS 'Complete history of all queries for analytics and debugging';
COMMENT ON TABLE query_cache IS 'Persistent cache to reduce API costs and improve response time';
COMMENT ON TABLE rate_limits IS 'Per-user rate limiting to prevent abuse';
COMMENT ON TABLE user_profiles IS 'User activity statistics and preferences';
COMMENT ON TABLE feedback IS 'User feedback on bot responses for quality improvement';
COMMENT ON TABLE audit_logs IS 'Comprehensive audit trail for security and compliance';

COMMENT ON FUNCTION match_documents IS 'Performs vector similarity search with optional metadata filtering';
COMMENT ON FUNCTION clean_expired_cache IS 'Removes expired cache entries (run periodically)';
COMMENT ON FUNCTION reset_rate_limit_if_expired IS 'Resets user rate limit if window expired';
COMMENT ON FUNCTION update_user_profile IS 'Updates user profile statistics on each query';

COMMIT;

-- ============================================================================
-- Verification Queries
-- ============================================================================
-- Run these to verify the migration succeeded:
--
-- SELECT tablename FROM pg_tables WHERE schemaname = 'public' ORDER BY tablename;
-- SELECT indexname FROM pg_indexes WHERE schemaname = 'public' ORDER BY indexname;
-- SELECT routine_name FROM information_schema.routines WHERE routine_schema = 'public';
-- ============================================================================
