# 📋 Guia de Migração - Schema Supabase Completo

## Visão Geral

Este guia descreve a migração do schema básico do Supabase para um schema completo de produção com:

✅ **Controle de Documentos** - Evita reprocessamento e rastreia arquivos
✅ **Analytics** - Histórico completo de queries e métricas
✅ **Cache Persistente** - Reduz custos de API
✅ **Rate Limiting** - Controle de uso por usuário
✅ **Perfis de Usuário** - Estatísticas e preferências
✅ **Feedback** - Sistema de avaliação de respostas
✅ **Audit Logs** - Trilha de auditoria completa
✅ **Row Level Security** - Políticas de segurança

---

## 🎯 Benefícios

### Redução de Custos
- **40-60% menos chamadas de API** (cache persistente)
- **Evita reprocessamento de documentos** (controle de hash)
- **Otimização de embeddings** (deduplicação automática)

### Produção Ready
- **Segurança com RLS** policies
- **Audit trail completo**
- **Rate limiting robusto**
- **Escalabilidade garantida**

### Insights e Analytics
- **Rastreamento de uso por usuário**
- **Métricas de performance**
- **Análise de fontes de dados**
- **Histórico completo de queries**

---

## 📊 Schema Atual vs Novo

### Antes (Schema Básico)
```
documents (1 tabela)
├── id
├── content
├── embedding
└── metadata

Configurações: JSON local (server_config.json)
Cache: Em memória (perdido ao reiniciar)
Rate limit: Em memória
```

### Depois (Schema Completo)
```
documents (melhorado)
├── id, content, embedding, metadata
├── document_id, chunk_index
├── source_id → document_sources
└── created_at, updated_at

document_sources (NOVO - Controle de Documentos)
├── Evita reprocessamento
├── Hash SHA-256 para detecção de mudanças
├── Estatísticas de tokens e chunks
└── Controle de versões

server_configs (NOVO)
query_history (NOVO)
query_cache (NOVO)
rate_limits (NOVO)
user_profiles (NOVO)
feedback (NOVO)
audit_logs (NOVO)
document_processing_log (NOVO)
```

---

## 🚀 Passo a Passo da Migração

### Pré-requisitos

1. **Backup completo:**
```bash
# Backup do banco de dados
pg_dump -h sua-url.supabase.co -U postgres -d postgres > backup_$(date +%Y%m%d_%H%M%S).sql

# Backup do arquivo de configuração
cp server_config.json server_config.json.backup
```

2. **Ambiente de teste** (recomendado):
   - Crie um projeto Supabase separado para testes
   - Teste a migração completamente antes de aplicar em produção

### Passo 1: Core Schema (Obrigatório)

```bash
# Conectar ao Supabase
psql -h sua-url.supabase.co -U postgres -d postgres

# Ou use o SQL Editor no dashboard Supabase
```

Execute no SQL Editor:
```sql
-- Copie e cole o conteúdo de:
migrations/001_enhanced_schema.sql
```

**Tempo estimado:** 2-5 minutos
**Risk Level:** LOW

✅ **Verificação:**
```sql
SELECT tablename FROM pg_tables WHERE schemaname = 'public' ORDER BY tablename;
-- Deve mostrar: documents, server_configs, query_history, etc.
```

### Passo 2: Row Level Security (Obrigatório)

```sql
-- Copie e cole o conteúdo de:
migrations/002_row_level_security.sql
```

**Tempo estimado:** 1-2 minutos
**Risk Level:** LOW

✅ **Verificação:**
```sql
SELECT schemaname, tablename, rowsecurity
FROM pg_tables
WHERE schemaname = 'public';
-- rowsecurity deve ser 'true' para todas as tabelas
```

### Passo 3: Document Control System (Obrigatório)

```sql
-- Copie e cole o conteúdo de:
migrations/003_document_control_system.sql
```

**Tempo estimado:** 2-3 minutos
**Risk Level:** LOW

✅ **Verificação:**
```sql
SELECT * FROM get_knowledge_base_stats();
-- Deve retornar estatísticas (zeradas se sem dados)
```

### Passo 4: Validação Completa (Recomendado)

```bash
psql -h sua-url.supabase.co -U postgres -d postgres -f migrations/validate.sql
```

**Esperado:**
```
VALIDATION SUMMARY
============================================================
Total Tests: 50+
Passed: 50+
Failed: 0
Success Rate: 100%
✓ All validation tests passed!
```

---

## 🔄 Migração de Dados

### Migrar Configurações do JSON para Database

Se você tem configurações em `server_config.json`:

```python
# Execute este script Python:
python migrations/migrate_config.py
```

Ou manualmente no SQL:
```sql
INSERT INTO server_configs (guild_id, filter_level, settings)
VALUES
    ('123456789', 'moderado', '{}'::jsonb),
    ('987654321', 'liberal', '{}'::jsonb);
```

### Reprocessar Documentos (Opcional)

Se quiser popular o sistema de controle de documentos:

```bash
# Isso vai registrar todos os documentos existentes
python load.py --reindex
```

O novo `load.py` automaticamente:
- ✅ Calcula hash SHA-256 de cada arquivo
- ✅ Verifica se já foi processado
- ✅ Pula arquivos duplicados
- ✅ Registra estatísticas de tokens
- ✅ Cria log de processamento

---

## 🔍 Verificação Pós-Migração

### 1. Testar Conexão do Bot

```bash
python bot.py
```

Deve mostrar:
```
[INFO] 🔄 Iniciando carregamento do RAG...
[INFO] ✅ RAG carregado | Modelo: minimax/minimax-m2:free | K_DOCS: 5
[INFO] 🤖 Bot iniciado | Nome: SeuBot#1234 | Servidores: 2
```

### 2. Testar Query

No Discord:
```
/ask pergunta: Teste após migração
```

Verificar nos logs:
```
[INFO] 💬 CMD /ask | Servidor: 123 | Usuário: 456 | Pergunta: Teste...
[INFO] ✅ Resposta enviada | Fontes: 3
```

### 3. Verificar Database

```sql
-- Estatísticas da base de conhecimento
SELECT * FROM get_knowledge_base_stats();

-- Documentos ativos
SELECT * FROM active_documents;

-- Últimas queries
SELECT user_id, question, created_at
FROM query_history
ORDER BY created_at DESC
LIMIT 10;

-- Cache hit rate
SELECT
    COUNT(*) FILTER (WHERE hit_count > 0) * 100.0 / COUNT(*) AS cache_hit_rate
FROM query_cache;
```

---

## 🎨 Novos Recursos Disponíveis

### 1. Controle de Documentos

```python
from src.services.document_control_service import DocumentControlService

# Verificar se documento já foi processado
should_process, message = doc_service.should_process_file(file_path)
if not should_process:
    print(f"⏭️  Pulando: {message}")

# Estatísticas da base
stats = doc_service.get_knowledge_base_stats()
print(f"📊 Total: {stats['active_sources']} documentos")
print(f"📦 Chunks: {stats['total_chunks']}")
print(f"💰 Tokens: {stats['total_tokens']}")
```

### 2. Analytics de Queries

```sql
-- Top usuários
SELECT user_id, COUNT(*) as queries
FROM query_history
WHERE created_at > NOW() - INTERVAL '7 days'
GROUP BY user_id
ORDER BY queries DESC
LIMIT 10;

-- Tempo médio de resposta
SELECT AVG(response_time_ms) as avg_ms
FROM query_history
WHERE created_at > NOW() - INTERVAL '24 hours';

-- Queries mais comuns (similar)
SELECT LEFT(question, 50) as query, COUNT(*) as count
FROM query_history
GROUP BY LEFT(question, 50)
ORDER BY count DESC
LIMIT 10;
```

### 3. Admin Commands

Adicione ao bot comandos administrativos:

```python
@bot.tree.command(name="kb-stats")
async def kb_stats(interaction: discord.Interaction):
    """Mostra estatísticas da base de conhecimento"""
    stats = doc_service.get_knowledge_base_stats()

    embed = discord.Embed(title="📊 Base de Conhecimento")
    embed.add_field(name="Documentos", value=stats['active_sources'])
    embed.add_field(name="Chunks", value=stats['total_chunks'])
    embed.add_field(name="Tokens", value=f"{stats['total_tokens']:,}")
    embed.add_field(name="Tamanho", value=f"{stats['total_size_mb']:.2f} MB")

    await interaction.response.send_message(embed=embed)
```

---

## ⚠️ Problemas Comuns e Soluções

### Erro: "extension vector does not exist"

```sql
-- Solução:
CREATE EXTENSION IF NOT EXISTS vector;
```

### Erro: "relation documents already exists"

A migração está preparada para isso. Se quiser recria totalmente:
```sql
-- CUIDADO: Isso apaga dados!
DROP TABLE documents CASCADE;
-- Depois execute a migração novamente
```

### Erro: RLS bloqueando queries

Certifique-se de usar `service_role_key`, não `anon_key`:

```python
# Correto:
supabase = create_client(url, service_role_key)

# Errado:
supabase = create_client(url, anon_key)  # Vai ser bloqueado pelo RLS
```

### Bot não encontra configurações

```sql
-- Verifique se foram migradas:
SELECT * FROM server_configs;

-- Se estiver vazio, migre manualmente:
INSERT INTO server_configs (guild_id, filter_level)
VALUES ('dm', 'moderado');  -- Para DMs
```

---

## 🔙 Rollback

Se precisar reverter a migração:

```bash
psql -h sua-url.supabase.co -U postgres -d postgres -f migrations/rollback.sql
```

Isso irá:
1. ✅ Desabilitar RLS
2. ✅ Dropar policies
3. ✅ Dropar funções
4. ✅ Dropar tabelas novas
5. ✅ Manter tabela `documents` original

**ATENÇÃO:** Faça backup antes de fazer rollback!

Após rollback:
```bash
# Restaurar configurações
cp server_config.json.backup server_config.json

# Testar bot
python bot.py
```

---

## 📈 Métricas de Sucesso

Após 24 horas da migração, verifique:

- [ ] **Cache hit rate > 30%**
```sql
SELECT COUNT(*) FILTER (WHERE hit_count > 0)::FLOAT / COUNT(*) * 100
FROM query_cache;
```

- [ ] **Zero reprocessamentos desnecessários**
```sql
SELECT COUNT(*) FROM document_sources WHERE status = 'completed';
-- Deve ser igual ao número de arquivos únicos
```

- [ ] **Queries funcionando normalmente**
```sql
SELECT COUNT(*) FROM query_history
WHERE created_at > NOW() - INTERVAL '24 hours';
```

- [ ] **Sem erros nos logs**
```bash
grep "ERROR" logs/bot.log | wc -l
# Deve ser 0 ou muito baixo
```

---

## 🎯 Próximos Passos

Após migração bem-sucedida:

1. **Configurar limpeza automática de cache:**
```sql
-- Criar cronjob (Supabase → Database → Cron Jobs)
SELECT cron.schedule(
    'clean-expired-cache',
    '0 2 * * *',  -- Todo dia às 2 AM
    $$ SELECT clean_expired_cache(); $$
);
```

2. **Implementar dashboard de analytics**
3. **Adicionar mais admin commands**
4. **Configurar alertas de uso**
5. **Otimizar indexes baseado em uso real**

---

## 📞 Suporte

**Documentação completa:** `migrations/README.md`

**Arquivos importantes:**
- `migrations/001_enhanced_schema.sql` - Schema principal
- `migrations/002_row_level_security.sql` - Políticas RLS
- `migrations/003_document_control_system.sql` - Controle de documentos
- `migrations/validate.sql` - Testes de validação
- `migrations/rollback.sql` - Procedimento de rollback

**Validação:**
```bash
# Testa tudo
psql -h sua-url.supabase.co -U postgres -d postgres -f migrations/validate.sql
```

---

**Versão:** 1.0.0
**Data:** 2025-11-05
**Status:** ✅ Production Ready
