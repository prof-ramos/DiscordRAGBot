-- ============================================================================
-- Knowledge Base Vector Search Function
-- ============================================================================
-- Função RPC para busca vetorial otimizada nos chunks da base de conhecimento
-- ============================================================================

-- Criar função de busca vetorial
CREATE OR REPLACE FUNCTION match_kb_chunks(
  query_embedding vector(1536),
  match_threshold float DEFAULT 0.7,
  match_count int DEFAULT 5,
  filter_collection_id uuid DEFAULT NULL
)
RETURNS TABLE (
  chunk_id uuid,
  document_id uuid,
  document_title text,
  collection_name text,
  collection_id uuid,
  content text,
  chunk_index int,
  similarity float,
  doc_metadata jsonb
)
LANGUAGE sql STABLE
AS $$
  SELECT
    c.id AS chunk_id,
    c.document_id,
    d.title AS document_title,
    coll.name AS collection_name,
    coll.id AS collection_id,
    c.content,
    c.chunk_index,
    1 - (c.embedding <=> query_embedding) AS similarity,
    d.metadata AS doc_metadata
  FROM kb_chunks c
  JOIN kb_documents d ON c.document_id = d.id
  JOIN kb_collections coll ON d.collection_id = coll.id
  WHERE
    d.is_active = true
    AND d.is_indexed = true
    AND (filter_collection_id IS NULL OR coll.id = filter_collection_id)
    AND 1 - (c.embedding <=> query_embedding) > match_threshold
  ORDER BY c.embedding <=> query_embedding
  LIMIT match_count;
$$;

-- Criar índice IVFFlat para performance (se não existir)
CREATE INDEX IF NOT EXISTS idx_kb_chunks_embedding_ivfflat
ON kb_chunks
USING ivfflat (embedding vector_cosine_ops)
WITH (lists = 100);

-- Adicionar constraint única para evitar duplicatas (collection_id, external_id)
ALTER TABLE kb_documents
DROP CONSTRAINT IF EXISTS kb_documents_collection_external_unique;

ALTER TABLE kb_documents
ADD CONSTRAINT kb_documents_collection_external_unique
UNIQUE (collection_id, external_id);

-- Adicionar coluna content_hash se não existir
ALTER TABLE kb_documents
ADD COLUMN IF NOT EXISTS content_hash text;

-- Criar índice para content_hash
CREATE INDEX IF NOT EXISTS idx_kb_documents_content_hash
ON kb_documents(content_hash);

-- Comentários para documentação
COMMENT ON FUNCTION match_kb_chunks IS 'Busca vetorial por similaridade nos chunks da base de conhecimento';
COMMENT ON INDEX idx_kb_chunks_embedding_ivfflat IS 'Índice IVFFlat para busca vetorial otimizada';
COMMENT ON CONSTRAINT kb_documents_collection_external_unique ON kb_documents IS 'Garante que não haja documentos duplicados na mesma coleção';
