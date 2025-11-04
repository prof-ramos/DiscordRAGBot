# Troubleshooting

## Problemas Comuns

### Bot Não Conecta

#### Erro: `Improper token has been passed`

**Mensagem completa**:
```
discord.errors.LoginFailure: Improper token has been passed.
```

**Causa**: Token Discord inválido ou incorreto.

**Soluções**:

1. **Verificar `.env`**:
```bash
cat .env | grep DISCORD_TOKEN
```

2. **Regenerar token**:
   - Discord Developer Portal → Bot → Reset Token
   - Copiar novo token
   - Atualizar `.env`

3. **Verificar formato**:
   - Token deve começar com `MTIzNDU2...`
   - Sem espaços ou quebras de linha
   - Sem aspas extras

**Exemplo correto**:
```bash
DISCORD_TOKEN=MTIzNDU2Nzg5MDEyMzQ1Njc4OQ.GaBcDe.FgHiJkLmNoPqRsTuVwXyZ
```

---

#### Erro: `403 Forbidden`

**Mensagem completa**:
```
discord.errors.Forbidden: 403 Forbidden (error code: 40001)
```

**Causa**: Bot sem permissões necessárias.

**Soluções**:

1. **Verificar intents**:
   - Discord Developer Portal → Bot
   - Ativar **MESSAGE CONTENT INTENT**
   - Ativar **SERVER MEMBERS INTENT** (opcional)

2. **Reconvidar bot**:
   - OAuth2 → URL Generator
   - Selecionar scopes: `bot`, `applications.commands`
   - Selecionar permissões necessárias
   - Usar nova URL para reconvidar

---

### RAG Não Carrega

#### Erro: `Vectorstore não encontrado`

**Mensagem completa**:
```
[⚠️] Vectorstore não encontrado em 'vectorstore/'
[💡] Execute 'python load.py' primeiro para indexar seus documentos
```

**Causa**: Vector store não foi criado.

**Soluções**:

1. **Executar indexação**:
```bash
python load.py
```

2. **Verificar pasta `data/`**:
```bash
ls -la data/
```

3. **Verificar se PDFs existem**:
```bash
ls -la data/*.pdf
```

4. **Verificar vector store criado**:
```bash
ls -la vectorstore/
```

---

#### Erro: `OPENAI_API_KEY não encontrada`

**Mensagem completa**:
```
ValueError: OPENAI_API_KEY não encontrada no .env
```

**Causa**: Chave OpenAI não configurada.

**Soluções**:

1. **Adicionar ao `.env`**:
```bash
echo "OPENAI_API_KEY=sk-proj-..." >> .env
```

2. **Verificar arquivo**:
```bash
cat .env | grep OPENAI_API_KEY
```

3. **Verificar validade da chave**:
   - OpenAI Platform → API Keys
   - Verificar se chave está ativa
   - Regenerar se necessário

---

### Erros de Indexação

#### Erro: `Nenhum PDF encontrado`

**Mensagem completa**:
```
[❌] Nenhum arquivo PDF encontrado em 'data'
[💡] Adicione arquivos .pdf na pasta 'data'
```

**Causa**: Pasta `data/` vazia ou sem PDFs.

**Soluções**:

1. **Criar pasta**:
```bash
mkdir -p data
```

2. **Adicionar PDFs**:
```bash
cp /caminho/para/documento.pdf data/
```

3. **Verificar extensão**:
   - Arquivos devem ter extensão `.pdf`
   - Case-sensitive em Linux

---

#### Erro: `Timeout durante indexação`

**Mensagem completa**:
```
openai.error.Timeout: Request timed out
```

**Causa**: Conexão lenta ou muitos documentos.

**Soluções**:

1. **Verificar conexão**:
```bash
ping api.openai.com
```

2. **Processar em lotes menores**:
   - Indexar poucos PDFs por vez
   - Remover PDFs temporariamente

3. **Aumentar timeout** (em `load.py`):
```python
embeddings = OpenAIEmbeddings(
    model="text-embedding-3-small",
    request_timeout=60  # Aumentar de 30 para 60
)
```

---

### Erros de Comandos

#### Erro: `Slash commands não aparecem`

**Causa**: Comandos não sincronizados.

**Soluções**:

1. **Verificar logs**:
```bash
grep "sincronizados" logs/bot.log
```

2. **Reiniciar bot**:
```bash
# Ctrl+C para parar
python bot.py
```

3. **Aguardar propagação**:
   - Comandos podem levar até 1 hora
   - Para comandos imediatos: adicione `guild_id`

4. **Reconvidar bot**:
   - Com scope `applications.commands`

---

#### Erro: `/config` não funciona para admin

**Mensagem**:
```
❌ Apenas administradores podem alterar as configurações do bot!
```

**Causa**: Permissões incorretas.

**Soluções**:

1. **Verificar permissões no servidor**:
   - Usuário deve ter permissão **Administrador**
   - Ou ter papel com permissão de admin

2. **Verificar em DM**:
   - `/config` funciona em DM sem restrições

3. **Ver logs**:
```bash
grep "Acesso negado /config" logs/bot.log
```

---

### Erros de Respostas

#### Bot não responde

**Causa possíveis**:
1. RAG não carregado
2. Timeout na API
3. Bot sem permissões

**Diagnóstico**:

1. **Ver logs**:
```bash
tail -f logs/bot.log
```

2. **Testar manualmente**:
```python
# No console Python
from bot import processar_pergunta
resposta = await processar_pergunta("teste")
print(resposta)
```

3. **Verificar status**:
```
/status
```

**Soluções**:
- Se RAG não carregado: `python load.py`
- Se timeout: Verificar OpenRouter/OpenAI status
- Se sem permissões: Reconvidar bot

---

#### Respostas genéricas (sem contexto)

**Sintoma**: Bot responde, mas sem usar documentos.

**Causa**: Busca vetorial não retorna resultados relevantes.

**Soluções**:

1. **Verificar pergunta**:
   - Use termos presentes nos PDFs
   - Seja mais específico

2. **Ajustar K_DOCS** (em `bot.py`):
```python
K_DOCS = 10  # Aumentar de 5 para 10
```

3. **Reindexar com chunks menores** (em `load.py`):
```python
chunk_size=800,      # Reduzir de 1000
chunk_overlap=150,   # Reduzir de 200
```

4. **Verificar qualidade dos PDFs**:
   - PDFs devem ter texto extraível
   - Não podem ser imagens escaneadas

---

### Erros de API

#### Erro: `Rate limit exceeded`

**Mensagem completa**:
```
openai.error.RateLimitError: Rate limit reached
```

**Causa**: Muitas requisições em pouco tempo.

**Soluções**:

1. **Aguardar** (rate limit reseta em minutos)

2. **Usar modelo gratuito** (OpenRouter):
```bash
OPENROUTER_MODEL=minimax/minimax-m2:free
```

3. **Implementar rate limiting**:
```python
import time
from functools import wraps

def rate_limit(max_per_minute):
    min_interval = 60.0 / max_per_minute
    last_called = [0.0]
    
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            elapsed = time.time() - last_called[0]
            left_to_wait = min_interval - elapsed
            if left_to_wait > 0:
                await asyncio.sleep(left_to_wait)
            result = await func(*args, **kwargs)
            last_called[0] = time.time()
            return result
        return wrapper
    return decorator
```

---

#### Erro: `Invalid API key`

**Mensagem completa**:
```
openai.error.AuthenticationError: Invalid API key
```

**Causa**: Chave API inválida ou expirada.

**Soluções**:

1. **Verificar chave**:
```bash
cat .env | grep API_KEY
```

2. **Testar chave**:
```bash
curl https://api.openai.com/v1/models \
  -H "Authorization: Bearer $OPENAI_API_KEY"
```

3. **Regenerar chaves**:
   - OpenAI Platform → API Keys
   - OpenRouter → Settings → API Keys

---

### Problemas de Performance

#### Bot lento para responder

**Causas**:
1. Muitos documentos recuperados
2. Modelo LLM lento
3. Chunks muito grandes

**Soluções**:

1. **Reduzir K_DOCS**:
```python
K_DOCS = 3  # Reduzir de 5
```

2. **Usar modelo mais rápido**:
```bash
OPENROUTER_MODEL=google/gemini-flash-1.5
```

3. **Reduzir max_tokens**:
```python
model_kwargs={"max_tokens": 500}  # Reduzir de 1000
```

4. **Cache de respostas** (implementar):
```python
from functools import lru_cache

@lru_cache(maxsize=100)
def cached_embeddings(text):
    return embeddings.embed_query(text)
```

---

#### Alto uso de memória

**Sintoma**: Bot consome muita RAM.

**Causas**:
1. Vector store grande em memória
2. Muitos chunks carregados

**Soluções**:

1. **Verificar uso**:
```bash
ps aux | grep python
```

2. **Reduzir chunks**:
   - Indexar menos PDFs
   - Usar chunks maiores (menos quantidade)

3. **Usar lazy loading** (Chroma suporta):
```python
db = Chroma(
    persist_directory=INDEX_PATH,
    embedding_function=embeddings,
    collection_metadata={"hnsw:space": "cosine"}
)
```

---

## Logs de Debugging

### Ativar Debug Mode

Em `bot.py`, alterar:

```python
logging.basicConfig(
    level=logging.DEBUG,  # Alterar de INFO
    ...
)
```

### Ver Logs Detalhados

```bash
tail -f logs/bot.log | grep -E "DEBUG|ERROR"
```

### Logs Específicos

**LangChain**:
```python
from langchain.globals import set_debug
set_debug(True)
```

**Discord.py**:
```python
logging.getLogger('discord').setLevel(logging.DEBUG)
```

---

## Ferramentas de Diagnóstico

### Verificar Conectividade

```bash
# Discord
ping discord.com

# OpenAI
curl -I https://api.openai.com/v1/models

# OpenRouter
curl -I https://openrouter.ai/api/v1/models
```

### Verificar Variáveis de Ambiente

```bash
python -c "from dotenv import load_dotenv; import os; load_dotenv(); print('DISCORD_TOKEN:', bool(os.getenv('DISCORD_TOKEN'))); print('OPENAI_API_KEY:', bool(os.getenv('OPENAI_API_KEY')))"
```

### Testar Componentes Isoladamente

**Embeddings**:
```python
from langchain_openai import OpenAIEmbeddings
embeddings = OpenAIEmbeddings()
result = embeddings.embed_query("teste")
print(f"Embedding gerado: {len(result)} dimensões")
```

**Chroma**:
```python
from langchain_community.vectorstores import Chroma
db = Chroma(persist_directory="vectorstore")
results = db.similarity_search("teste", k=1)
print(f"Resultados: {len(results)}")
```

**LLM**:
```python
from langchain_openai import ChatOpenAI
llm = ChatOpenAI(
    model="minimax/minimax-m2:free",
    api_key=os.getenv("OPENROUTER_API_KEY"),
    base_url="https://openrouter.ai/api/v1"
)
response = llm.invoke("Olá")
print(response.content)
```

---

## Quando Pedir Ajuda

Se nenhuma solução funcionou:

1. **Coletar informações**:
```bash
# Versão Python
python --version

# Versões de pacotes
pip freeze > installed_packages.txt

# Últimos logs
tail -n 100 logs/bot.log > recent_logs.txt

# Sistema operacional
uname -a
```

2. **Descrever problema**:
   - O que tentou fazer
   - O que esperava
   - O que aconteceu
   - Logs relevantes
   - Passos para reproduzir

3. **Onde pedir ajuda**:
   - GitHub Issues (se aplicável)
   - Discord de suporte
   - Stack Overflow
   - Documentação oficial das bibliotecas

---

## Problemas Conhecidos

### PyNaCl Warning

**Mensagem**:
```
WARNING: PyNaCl is not installed, voice will NOT be supported
```

**Impacto**: Nenhum (bot não usa voz)

**Solução**: Ignorar ou instalar:
```bash
pip install pynacl
```

### Chroma Telemetry

**Mensagem**:
```
INFO: Anonymized telemetry enabled
```

**Impacto**: Nenhum

**Solução**: Desabilitar (opcional):
```python
import os
os.environ["ANONYMIZED_TELEMETRY"] = "False"
```

---

## Recuperação de Desastres

### Resetar Tudo

```bash
# 1. Parar bot (Ctrl+C)

# 2. Limpar vector store
rm -rf vectorstore/

# 3. Limpar logs
rm -rf logs/

# 4. Limpar configurações
rm -f server_config.json

# 5. Reinstalar dependências
pip install -r requirements.txt --force-reinstall

# 6. Reindexar
python load.py

# 7. Reiniciar bot
python bot.py
```

### Backup

**Antes de mudanças importantes**:
```bash
# Backup vector store
tar -czf vectorstore-backup.tar.gz vectorstore/

# Backup configurações
cp server_config.json server_config.json.bak

# Backup logs importantes
cp logs/bot.log logs/bot.log.$(date +%Y%m%d)
```

---

## Próximos Passos

✅ Problemas resolvidos!

👉 Volte para [Instalação](installation.md) se precisa reinstalar  
👉 Consulte [Referência API](api.md) para entender funções  
👉 Veja [Logs](logs.md) para monitoramento
