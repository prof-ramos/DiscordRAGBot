-- ============================================================================
-- Discord RAG Bot - Document Control System
-- ============================================================================
-- Migration: 003_document_control_system.sql
-- Description: Sistema de controle de documentos processados
-- Author: Supabase Schema Architect
-- Date: 2025-11-05
-- Risk Level: LOW
--
-- Funcionalidades:
-- - Rastreamento de arquivos processados (evita reprocessamento)
-- - Detecção de alterações em arquivos (hash SHA-256)
-- - Status do processamento (pending, processing, completed, failed)
-- - Estatísticas de tokens e chunks
-- - Controle da base de conhecimento
-- - Histórico de versões de documentos
-- - Gerenciamento de fontes de dados
-- ============================================================================

BEGIN;

-- ============================================================================
-- Table: document_sources
-- ============================================================================
-- Rastreia arquivos de origem e evita reprocessamento
-- ============================================================================

CREATE TABLE IF NOT EXISTS document_sources (
    id BIGSERIAL PRIMARY KEY,

    -- Identificação do arquivo
    file_name TEXT NOT NULL,
    file_path TEXT NOT NULL,
    file_hash VARCHAR(64) NOT NULL, -- SHA-256 hash para detectar mudanças
    file_size BIGINT NOT NULL, -- Tamanho em bytes

    -- Informações do arquivo
    file_type VARCHAR(50) NOT NULL, -- pdf, txt, docx, etc.
    mime_type VARCHAR(100),

    -- Status do processamento
    status VARCHAR(20) DEFAULT 'pending' NOT NULL,
    -- pending: aguardando processamento
    -- processing: em processamento
    -- completed: processado com sucesso
    -- failed: falha no processamento
    -- outdated: arquivo foi modificado (hash diferente)

    -- Estatísticas
    total_chunks INTEGER DEFAULT 0,
    total_tokens INTEGER DEFAULT 0, -- Tokens aproximados consumidos
    total_characters INTEGER DEFAULT 0,
    total_pages INTEGER,

    -- Processamento
    processed_at TIMESTAMPTZ,
    processing_started_at TIMESTAMPTZ,
    processing_duration_ms INTEGER, -- Duração do processamento em ms

    -- Controle de versão
    version INTEGER DEFAULT 1,
    previous_version_id BIGINT REFERENCES document_sources(id) ON DELETE SET NULL,

    -- Erros (se falhou)
    error_message TEXT,
    error_details JSONB,

    -- Metadados adicionais
    metadata JSONB DEFAULT '{}'::jsonb,

    -- Controle de acesso
    is_active BOOLEAN DEFAULT true, -- Se falso, chunks relacionados são "desativados"
    uploaded_by VARCHAR(50), -- Discord user ID que fez upload

    -- Rastreamento
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),

    -- Constraints
    CONSTRAINT document_sources_status_valid
        CHECK (status IN ('pending', 'processing', 'completed', 'failed', 'outdated')),
    CONSTRAINT document_sources_file_size_positive CHECK (file_size > 0),
    CONSTRAINT document_sources_total_chunks_positive CHECK (total_chunks >= 0),
    CONSTRAINT document_sources_version_positive CHECK (version > 0)
);

-- Índices
CREATE UNIQUE INDEX IF NOT EXISTS document_sources_file_hash_idx
    ON document_sources(file_hash)
    WHERE is_active = true AND status = 'completed';

CREATE INDEX IF NOT EXISTS document_sources_file_name_idx ON document_sources(file_name);
CREATE INDEX IF NOT EXISTS document_sources_status_idx ON document_sources(status);
CREATE INDEX IF NOT EXISTS document_sources_created_at_idx ON document_sources(created_at DESC);
CREATE INDEX IF NOT EXISTS document_sources_processed_at_idx ON document_sources(processed_at DESC);
CREATE INDEX IF NOT EXISTS document_sources_is_active_idx ON document_sources(is_active);

-- Índice composto para buscas comuns
CREATE INDEX IF NOT EXISTS document_sources_status_active_idx
    ON document_sources(status, is_active);

-- ============================================================================
-- Atualizar tabela documents para referenciar source
-- ============================================================================

-- Adicionar coluna de referência à source
ALTER TABLE documents
ADD COLUMN IF NOT EXISTS source_id BIGINT REFERENCES document_sources(id) ON DELETE SET NULL;

-- Índice para a foreign key
CREATE INDEX IF NOT EXISTS documents_source_id_idx ON documents(source_id);

-- ============================================================================
-- Table: document_processing_log
-- ============================================================================
-- Log detalhado de cada tentativa de processamento
-- ============================================================================

CREATE TABLE IF NOT EXISTS document_processing_log (
    id BIGSERIAL PRIMARY KEY,

    -- Referência ao documento
    source_id BIGINT NOT NULL REFERENCES document_sources(id) ON DELETE CASCADE,

    -- Status da tentativa
    status VARCHAR(20) NOT NULL, -- started, completed, failed
    operation VARCHAR(50) NOT NULL, -- initial_load, reprocess, update, delete

    -- Estatísticas da tentativa
    chunks_created INTEGER DEFAULT 0,
    chunks_updated INTEGER DEFAULT 0,
    chunks_deleted INTEGER DEFAULT 0,
    tokens_consumed INTEGER DEFAULT 0,
    processing_duration_ms INTEGER,

    -- Detalhes
    error_message TEXT,
    error_traceback TEXT,
    metadata JSONB DEFAULT '{}'::jsonb,

    -- Rastreamento
    started_at TIMESTAMPTZ DEFAULT NOW(),
    completed_at TIMESTAMPTZ,

    -- Constraints
    CONSTRAINT processing_log_status_valid
        CHECK (status IN ('started', 'completed', 'failed')),
    CONSTRAINT processing_log_chunks_positive
        CHECK (chunks_created >= 0 AND chunks_updated >= 0 AND chunks_deleted >= 0)
);

-- Índices
CREATE INDEX IF NOT EXISTS processing_log_source_id_idx ON document_processing_log(source_id);
CREATE INDEX IF NOT EXISTS processing_log_status_idx ON document_processing_log(status);
CREATE INDEX IF NOT EXISTS processing_log_started_at_idx ON document_processing_log(started_at DESC);

-- ============================================================================
-- Functions: Document Control
-- ============================================================================

-- Function: Verificar se arquivo já foi processado
CREATE OR REPLACE FUNCTION is_document_processed(
    p_file_hash VARCHAR(64)
)
RETURNS BOOLEAN
LANGUAGE plpgsql
AS $$
DECLARE
    v_exists BOOLEAN;
BEGIN
    SELECT EXISTS (
        SELECT 1 FROM document_sources
        WHERE file_hash = p_file_hash
        AND status = 'completed'
        AND is_active = true
    ) INTO v_exists;

    RETURN v_exists;
END;
$$;

-- Function: Obter documento por hash
CREATE OR REPLACE FUNCTION get_document_by_hash(
    p_file_hash VARCHAR(64)
)
RETURNS TABLE (
    id BIGINT,
    file_name TEXT,
    status VARCHAR(20),
    total_chunks INTEGER,
    processed_at TIMESTAMPTZ
)
LANGUAGE plpgsql
AS $$
BEGIN
    RETURN QUERY
    SELECT
        document_sources.id,
        document_sources.file_name,
        document_sources.status,
        document_sources.total_chunks,
        document_sources.processed_at
    FROM document_sources
    WHERE document_sources.file_hash = p_file_hash
    AND document_sources.is_active = true
    ORDER BY document_sources.created_at DESC
    LIMIT 1;
END;
$$;

-- Function: Marcar documento como desatualizado
CREATE OR REPLACE FUNCTION mark_document_outdated(
    p_file_hash VARCHAR(64)
)
RETURNS BIGINT
LANGUAGE plpgsql
AS $$
DECLARE
    v_source_id BIGINT;
BEGIN
    UPDATE document_sources
    SET status = 'outdated',
        updated_at = NOW()
    WHERE file_hash = p_file_hash
    AND status = 'completed'
    AND is_active = true
    RETURNING id INTO v_source_id;

    RETURN v_source_id;
END;
$$;

-- Function: Desativar documento e seus chunks
CREATE OR REPLACE FUNCTION deactivate_document(
    p_source_id BIGINT
)
RETURNS INTEGER
LANGUAGE plpgsql
AS $$
DECLARE
    v_chunks_deleted INTEGER;
BEGIN
    -- Marcar source como inativo
    UPDATE document_sources
    SET is_active = false,
        updated_at = NOW()
    WHERE id = p_source_id;

    -- Deletar chunks relacionados
    DELETE FROM documents
    WHERE source_id = p_source_id;

    GET DIAGNOSTICS v_chunks_deleted = ROW_COUNT;

    -- Log da operação
    INSERT INTO document_processing_log (
        source_id,
        status,
        operation,
        chunks_deleted,
        completed_at
    ) VALUES (
        p_source_id,
        'completed',
        'delete',
        v_chunks_deleted,
        NOW()
    );

    RETURN v_chunks_deleted;
END;
$$;

-- Function: Estatísticas da base de conhecimento
CREATE OR REPLACE FUNCTION get_knowledge_base_stats()
RETURNS TABLE (
    total_sources INTEGER,
    active_sources INTEGER,
    total_chunks INTEGER,
    total_tokens INTEGER,
    total_size_mb NUMERIC,
    last_update TIMESTAMPTZ
)
LANGUAGE plpgsql
AS $$
BEGIN
    RETURN QUERY
    SELECT
        COUNT(*)::INTEGER AS total_sources,
        COUNT(*) FILTER (WHERE is_active = true)::INTEGER AS active_sources,
        COALESCE(SUM(total_chunks), 0)::INTEGER AS total_chunks,
        COALESCE(SUM(total_tokens), 0)::INTEGER AS total_tokens,
        ROUND(COALESCE(SUM(file_size), 0)::NUMERIC / 1024 / 1024, 2) AS total_size_mb,
        MAX(processed_at) AS last_update
    FROM document_sources
    WHERE status = 'completed';
END;
$$;

-- Function: Iniciar processamento
CREATE OR REPLACE FUNCTION start_document_processing(
    p_file_name TEXT,
    p_file_path TEXT,
    p_file_hash VARCHAR(64),
    p_file_size BIGINT,
    p_file_type VARCHAR(50)
)
RETURNS BIGINT
LANGUAGE plpgsql
AS $$
DECLARE
    v_source_id BIGINT;
    v_existing_id BIGINT;
BEGIN
    -- Verificar se já existe documento com mesmo hash
    SELECT id INTO v_existing_id
    FROM document_sources
    WHERE file_hash = p_file_hash
    AND is_active = true
    ORDER BY created_at DESC
    LIMIT 1;

    IF v_existing_id IS NOT NULL THEN
        -- Atualizar status para processing
        UPDATE document_sources
        SET status = 'processing',
            processing_started_at = NOW(),
            updated_at = NOW()
        WHERE id = v_existing_id
        RETURNING id INTO v_source_id;
    ELSE
        -- Criar novo registro
        INSERT INTO document_sources (
            file_name,
            file_path,
            file_hash,
            file_size,
            file_type,
            status,
            processing_started_at
        ) VALUES (
            p_file_name,
            p_file_path,
            p_file_hash,
            p_file_size,
            p_file_type,
            'processing',
            NOW()
        ) RETURNING id INTO v_source_id;
    END IF;

    -- Log início do processamento
    INSERT INTO document_processing_log (
        source_id,
        status,
        operation
    ) VALUES (
        v_source_id,
        'started',
        'initial_load'
    );

    RETURN v_source_id;
END;
$$;

-- Function: Finalizar processamento com sucesso
CREATE OR REPLACE FUNCTION complete_document_processing(
    p_source_id BIGINT,
    p_chunks_created INTEGER,
    p_total_tokens INTEGER,
    p_processing_duration_ms INTEGER
)
RETURNS VOID
LANGUAGE plpgsql
AS $$
BEGIN
    -- Atualizar source
    UPDATE document_sources
    SET status = 'completed',
        total_chunks = p_chunks_created,
        total_tokens = p_total_tokens,
        processed_at = NOW(),
        processing_duration_ms = p_processing_duration_ms,
        updated_at = NOW()
    WHERE id = p_source_id;

    -- Log conclusão
    INSERT INTO document_processing_log (
        source_id,
        status,
        operation,
        chunks_created,
        tokens_consumed,
        processing_duration_ms,
        completed_at
    ) VALUES (
        p_source_id,
        'completed',
        'initial_load',
        p_chunks_created,
        p_total_tokens,
        p_processing_duration_ms,
        NOW()
    );
END;
$$;

-- Function: Falha no processamento
CREATE OR REPLACE FUNCTION fail_document_processing(
    p_source_id BIGINT,
    p_error_message TEXT,
    p_error_details JSONB DEFAULT NULL
)
RETURNS VOID
LANGUAGE plpgsql
AS $$
BEGIN
    -- Atualizar source
    UPDATE document_sources
    SET status = 'failed',
        error_message = p_error_message,
        error_details = p_error_details,
        updated_at = NOW()
    WHERE id = p_source_id;

    -- Log erro
    INSERT INTO document_processing_log (
        source_id,
        status,
        operation,
        error_message,
        completed_at
    ) VALUES (
        p_source_id,
        'failed',
        'initial_load',
        p_error_message,
        NOW()
    );
END;
$$;

-- ============================================================================
-- Triggers: Automatic updates
-- ============================================================================

-- Trigger para updated_at
DROP TRIGGER IF EXISTS update_document_sources_updated_at ON document_sources;
CREATE TRIGGER update_document_sources_updated_at
    BEFORE UPDATE ON document_sources
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- ============================================================================
-- Views: Convenience views
-- ============================================================================

-- View: Documentos ativos
CREATE OR REPLACE VIEW active_documents AS
SELECT
    id,
    file_name,
    file_type,
    file_size,
    total_chunks,
    total_tokens,
    processed_at,
    created_at
FROM document_sources
WHERE is_active = true
AND status = 'completed'
ORDER BY processed_at DESC;

-- View: Documentos pendentes
CREATE OR REPLACE VIEW pending_documents AS
SELECT
    id,
    file_name,
    file_path,
    file_type,
    status,
    created_at
FROM document_sources
WHERE is_active = true
AND status IN ('pending', 'processing')
ORDER BY created_at ASC;

-- View: Histórico de processamento
CREATE OR REPLACE VIEW processing_history AS
SELECT
    ds.id,
    ds.file_name,
    ds.status AS current_status,
    dpl.operation,
    dpl.status AS log_status,
    dpl.chunks_created,
    dpl.tokens_consumed,
    dpl.processing_duration_ms,
    dpl.started_at,
    dpl.completed_at
FROM document_sources ds
JOIN document_processing_log dpl ON ds.id = dpl.source_id
ORDER BY dpl.started_at DESC;

-- ============================================================================
-- RLS Policies
-- ============================================================================

ALTER TABLE document_sources ENABLE ROW LEVEL SECURITY;
ALTER TABLE document_processing_log ENABLE ROW LEVEL SECURITY;

-- Service role tem acesso total
CREATE POLICY document_sources_service_role_all
    ON document_sources
    FOR ALL
    TO service_role
    USING (true)
    WITH CHECK (true);

CREATE POLICY processing_log_service_role_all
    ON document_processing_log
    FOR ALL
    TO service_role
    USING (true)
    WITH CHECK (true);

-- Authenticated pode ver documentos ativos
CREATE POLICY document_sources_authenticated_read
    ON document_sources
    FOR SELECT
    TO authenticated
    USING (is_active = true);

-- ============================================================================
-- Comments: Documentation
-- ============================================================================

COMMENT ON TABLE document_sources IS
    'Controle de documentos processados - evita reprocessamento e gerencia base de conhecimento';

COMMENT ON TABLE document_processing_log IS
    'Log detalhado de cada tentativa de processamento de documentos';

COMMENT ON FUNCTION is_document_processed IS
    'Verifica se um arquivo (por hash) já foi processado';

COMMENT ON FUNCTION get_knowledge_base_stats IS
    'Retorna estatísticas completas da base de conhecimento';

COMMENT ON FUNCTION deactivate_document IS
    'Desativa documento e remove seus chunks do vectorstore';

COMMENT ON VIEW active_documents IS
    'View de documentos ativos e processados com sucesso';

COMMIT;

-- ============================================================================
-- Verification
-- ============================================================================
-- SELECT * FROM get_knowledge_base_stats();
-- SELECT * FROM active_documents;
-- SELECT * FROM pending_documents;
-- ============================================================================
