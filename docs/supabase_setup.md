# Configuração do Supabase para uso com RAG

Para usar o Supabase como vectorstore para o seu bot RAG Discord, você precisa configurar o banco de dados do Supabase corretamente.

## 1. Habilitar a extensão pgvector

Antes de tudo, você precisa habilitar a extensão `pgvector` no seu projeto Supabase:

1. Acesse o painel do Supabase
2. Vá até a aba de SQL
3. Execute o seguinte comando SQL:

```sql
CREATE EXTENSION IF NOT EXISTS vector;
```

## 2. Criar a tabela para armazenar documentos e embeddings

Você precisa criar uma tabela chamada `documents` (ou qualquer nome que você tenha especificado em `table_name` no código) para armazenar os chunks de documentos e seus embeddings:

```sql
CREATE TABLE documents (
  id BIGSERIAL PRIMARY KEY,
  content TEXT,
  embedding vector(1536), -- 1536 dimensões para embeddings OpenAI
  metadata JSONB
);

-- Índice para melhorar a performance de busca vetorial
CREATE INDEX documents_embedding_idx ON documents USING ivfflat (embedding vector_cosine_ops) WITH (lists = 100);
```

## 3. Criar função para busca de documentos similares

O LangChain espera uma função específica para buscar documentos similares. Crie a seguinte função:

```sql
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
```

## 4. Configuração no seu bot

Com a tabela e função criadas, você pode usar as variáveis de ambiente definidas no `.env`:

```
SUPABASE_URL=seu_supabase_url
SUPABASE_API_KEY=sua_supabase_anon_key
```

## Notas

- A dimensão do vetor (1536) assume que você está usando embeddings OpenAI `text-embedding-3-small`. Se usar outro modelo de embeddings, ajuste conforme necessário.
- Certifique-se de que sua API do Supabase tem permissões para ler e escrever na tabela `documents`.
- A função `match_documents` é usada pelo LangChain para realizar buscas de similaridade.

Após configurar o banco de dados, você pode executar `python load.py` para indexar seus documentos no Supabase.