# Referência API

## load.py - Indexação de Documentos

### `load_documents()`

Carrega todos os arquivos PDF da pasta `data/`.

**Assinatura**:
```python
def load_documents() -> List[Document]
```

**Retorno**:
- `List[Document]`: Lista de documentos carregados
- `[]`: Lista vazia se pasta não existe ou está vazia

**Comportamento**:
1. Verifica existência da pasta `data/`
2. Lista arquivos `*.pdf`
3. Usa `DirectoryLoader` com `PyPDFLoader`
4. Mostra progress bar durante carregamento
5. Retorna documentos com metadata

**Exemplo**:
```python
documents = load_documents()
print(f"Carregados {len(documents)} documentos")
```

---

### `split_documents(documents)`

Divide documentos em chunks menores.

**Assinatura**:
```python
def split_documents(documents: List[Document]) -> List[Document]
```

**Parâmetros**:
- `documents`: Lista de documentos a dividir

**Retorno**:
- `List[Document]`: Lista de chunks

**Configuração**:
```python
RecursiveCharacterTextSplitter(
    chunk_size=1000,         # Tamanho do chunk
    chunk_overlap=200,       # Overlap entre chunks
    length_function=len,     # Função de medida
    separators=["\n\n", "\n", " ", ""]  # Separadores hierárquicos
)
```

**Exemplo**:
```python
chunks = split_documents(documents)
print(f"Criados {len(chunks)} chunks")
```

---

### `create_embeddings()`

Configura OpenAI Embeddings API.

**Assinatura**:
```python
def create_embeddings() -> OpenAIEmbeddings
```

**Retorno**:
- `OpenAIEmbeddings`: Modelo de embeddings configurado

**Exceções**:
- `ValueError`: Se `OPENAI_API_KEY` não está definida

**Configuração**:
```python
OpenAIEmbeddings(
    model="text-embedding-3-small"
)
```

**Exemplo**:
```python
embeddings = create_embeddings()
# Usar com Chroma ou outra vector store
```

---

### `create_vectorstore(chunks, embeddings)`

Cria e persiste Chroma vector store.

**Assinatura**:
```python
def create_vectorstore(
    chunks: List[Document],
    embeddings: OpenAIEmbeddings
) -> Chroma
```

**Parâmetros**:
- `chunks`: Chunks de documentos
- `embeddings`: Modelo de embeddings

**Retorno**:
- `Chroma`: Vector store criado e persistido

**Diretório de persistência**: `vectorstore/`

**Exemplo**:
```python
vectorstore = create_vectorstore(chunks, embeddings)
print(f"Vector store criado em 'vectorstore/'")
```

---

## bot.py - Bot Discord

### Configuração

#### `carregar_configuracoes()`

Carrega configurações de servidores do JSON.

**Assinatura**:
```python
def carregar_configuracoes() -> dict
```

**Retorno**:
- `dict`: Dicionário de configurações
- `{}`: Dicionário vazio se arquivo não existe

**Estrutura do retorno**:
```python
{
    "123456789": {"nivel": "moderado"},
    "987654321": {"nivel": "liberal"}
}
```

---

#### `salvar_configuracoes(configs)`

Persiste configurações no JSON.

**Assinatura**:
```python
def salvar_configuracoes(configs: dict) -> None
```

**Parâmetros**:
- `configs`: Dicionário de configurações

**Efeitos**:
- Escreve `server_config.json` com encoding UTF-8
- Formata com `indent=2` para legibilidade
- Usa `ensure_ascii=False` para caracteres especiais

**Exemplo**:
```python
configs = carregar_configuracoes()
configs["123456789"] = {"nivel": "conservador"}
salvar_configuracoes(configs)
```

---

#### `obter_nivel_servidor(guild_id)`

Retorna nível de filtro configurado.

**Assinatura**:
```python
def obter_nivel_servidor(guild_id: Optional[int]) -> str
```

**Parâmetros**:
- `guild_id`: ID do servidor (ou `None` para DM)

**Retorno**:
- `str`: "conservador", "moderado" (padrão), ou "liberal"

**Exemplo**:
```python
nivel = obter_nivel_servidor(123456789)
print(f"Nível: {nivel}")  # "moderado"
```

---

#### `definir_nivel_servidor(guild_id, nivel)`

Define nível de filtro e registra log.

**Assinatura**:
```python
def definir_nivel_servidor(
    guild_id: Optional[int],
    nivel: str
) -> None
```

**Parâmetros**:
- `guild_id`: ID do servidor (ou `None` para DM)
- `nivel`: "conservador", "moderado" ou "liberal"

**Efeitos**:
- Atualiza `server_config.json`
- Registra log: `"📝 Configuração alterada | Servidor: {guild_id} | Novo nível: {nivel}"`

**Exemplo**:
```python
definir_nivel_servidor(123456789, "liberal")
```

---

### Processamento

#### `processar_pergunta(question, guild_id, user_id, tipo)`

Processa pergunta através do pipeline RAG.

**Assinatura**:
```python
async def processar_pergunta(
    question: str,
    guild_id: Optional[int] = None,
    user_id: Optional[int] = None,
    tipo: str = "RAG"
) -> tuple[str, list]
```

**Parâmetros**:
- `question`: Pergunta do usuário
- `guild_id`: ID do servidor (opcional)
- `user_id`: ID do usuário (opcional)
- `tipo`: Tipo de interação ("CMD /ask", "Menção", "DM")

**Retorno**:
- `tuple[str, list]`: (resposta, fontes)
  - `resposta`: Texto da resposta gerada
  - `fontes`: Lista de `Document` com metadata

**Workflow**:
1. Verifica se RAG está carregado
2. Obtém nível de filtro do servidor
3. Seleciona prompt apropriado
4. Cria chain de recuperação + geração
5. Invoca chain com pergunta
6. Extrai resposta e fontes
7. Registra logs

**Exceções**:
- Retorna mensagem de erro se RAG não carregado
- Captura exceções e retorna erro formatado

**Logs**:
```
INFO: "💬 {tipo} | {guild_info} | Usuário: {user_id} | Nível: {nivel} | Pergunta: {question[:50]}..."
INFO: "✅ Resposta enviada | {guild_info} | Usuário: {user_id} | Fontes: {len(fontes)}"
ERROR: "❌ Erro ao processar | {guild_info} | Usuário: {user_id} | Erro: {str(e)}"
```

**Exemplo**:
```python
resposta, fontes = await processar_pergunta(
    "O que é RAG?",
    guild_id=123456789,
    user_id=987654321,
    tipo="CMD /ask"
)
```

---

#### `enviar_resposta_longa(channel, resposta, fontes)`

Divide e envia respostas longas.

**Assinatura**:
```python
async def enviar_resposta_longa(
    channel: discord.TextChannel,
    resposta: str,
    fontes: list
) -> None
```

**Parâmetros**:
- `channel`: Canal Discord para enviar
- `resposta`: Texto da resposta
- `fontes`: Lista de documentos fonte

**Comportamento**:
1. Se `resposta <= 2000 chars`: Envia direto
2. Se `resposta > 2000 chars`: Divide em chunks de 2000
3. Envia cada chunk sequencialmente
4. Se houver fontes: Formata e envia (top 3)

**Formato de fontes**:
```
📚 Fontes:
1. `documento1.pdf`
2. `documento2.pdf`
3. `documento3.pdf`
```

**Exemplo**:
```python
await enviar_resposta_longa(
    message.channel,
    resposta_longa,
    fontes
)
```

---

### Eventos Discord

#### `on_ready()`

Executado quando bot conecta.

**Assinatura**:
```python
@bot.event
async def on_ready() -> None
```

**Efeitos**:
1. Log: `"🤖 Bot iniciado | Nome: {bot.user} | Servidores: {len(bot.guilds)}"`
2. Sincroniza slash commands
3. Log: `"⚙️ Comandos sincronizados | Total: {len(synced)}"`
4. Captura e loga exceções de sincronização

---

#### `on_message(message)`

Processa mensagens recebidas.

**Assinatura**:
```python
@bot.event
async def on_message(message: discord.Message) -> None
```

**Parâmetros**:
- `message`: Mensagem Discord

**Comportamento**:
1. **Ignora**: Mensagens do próprio bot
2. **Processa comandos**: `await bot.process_commands(message)`
3. **Menções**: Se bot mencionado (não @everyone)
   - Extrai pergunta
   - Chama `processar_pergunta()`
   - Envia resposta via `enviar_resposta_longa()`
4. **DMs**: Se canal é DM
   - Chama `processar_pergunta()`
   - Envia resposta via `enviar_resposta_longa()`

**Logs**:
```
INFO: "📩 Menção | Servidor: {guild_id} | Usuário: {user_id}"
INFO: "📨 DM recebida | Usuário: {user_id}"
```

---

#### `on_error(event, *args, **kwargs)`

Handler global de erros.

**Assinatura**:
```python
@bot.event
async def on_error(event: str, *args, **kwargs) -> None
```

**Parâmetros**:
- `event`: Nome do evento
- `*args`: Argumentos do evento
- `**kwargs`: Keyword arguments do evento

**Efeitos**:
- Imprime erro no console
- Loga com stack trace completo: `"❌ Erro no evento {event} | Args: {args}"`

---

### Comandos Slash

#### `/ask`

Comando principal para fazer perguntas.

**Assinatura**:
```python
@bot.tree.command(name="ask", description="Faz uma pergunta ao RAG")
@app_commands.describe(pergunta="Sua pergunta")
async def ask(
    interaction: discord.Interaction,
    pergunta: str
) -> None
```

**Parâmetros**:
- `interaction`: Interação Discord
- `pergunta`: Pergunta do usuário

**Workflow**:
1. `await interaction.response.defer(thinking=True)`
2. Extrai `guild_id` e `user_id`
3. Log: `"🔹 Comando /ask | Servidor: {guild_id} | Usuário: {user_id}"`
4. Chama `processar_pergunta()`
5. Envia resposta via `interaction.followup.send()`
6. Envia fontes (se houver)

---

#### `/config`

Configura nível de filtro (apenas admins).

**Assinatura**:
```python
@bot.tree.command(name="config", description="Configura o nível de filtro")
@app_commands.describe(nivel="Escolha o nível")
@app_commands.choices(nivel=[...])
async def config(
    interaction: discord.Interaction,
    nivel: app_commands.Choice[str]
) -> None
```

**Parâmetros**:
- `interaction`: Interação Discord
- `nivel`: Choice (conservador, moderado, liberal)

**Validação**:
1. Se servidor: Verifica se usuário é administrador
2. Se não admin: Retorna erro ephemeral

**Workflow**:
1. Log: `"🔹 Comando /config | Servidor: {guild_id} | Usuário: {user_id} | Tentativa: {nivel.value}"`
2. Valida permissões
3. Se negado: Log WARNING
4. Se autorizado: Chama `definir_nivel_servidor()`
5. Envia confirmação

---

#### `/status`

Mostra configurações atuais.

**Assinatura**:
```python
@bot.tree.command(name="status", description="Mostra configurações")
async def status(interaction: discord.Interaction) -> None
```

**Parâmetros**:
- `interaction`: Interação Discord

**Workflow**:
1. Log: `"🔹 Comando /status | Servidor: {guild_id} | Usuário: {user_id}"`
2. Obtém nível atual via `obter_nivel_servidor()`
3. Cria embed com informações:
   - Nível de filtro
   - Modelo LLM
   - Status do RAG
4. Envia embed

**Embed**:
```
⚙️ Configurações do Bot
━━━━━━━━━━━━━━━━━━━━━
Nível de Filtro: ⚖️ MODERADO
Modelo LLM: minimax/minimax-m2:free
RAG Status: ✅ Ativo
```

---

## Constantes

### `DISCORD_TOKEN`
Token do bot Discord (variável de ambiente).

### `OPENAI_API_KEY`
Chave API OpenAI para embeddings (variável de ambiente).

### `OPENROUTER_API_KEY`
Chave API OpenRouter para LLM (variável de ambiente).

### `OPENROUTER_MODEL`
Modelo LLM a usar (variável de ambiente, padrão: `"anthropic/claude-3.5-sonnet"`).

### `INDEX_PATH`
Caminho do vector store (`"vectorstore"`).

### `K_DOCS`
Número de documentos a recuperar (padrão: `5`).

### `CONFIG_FILE`
Arquivo de configurações (`"server_config.json"`).

### `PROMPTS_POR_NIVEL`
Dicionário com prompts para cada nível:
```python
{
    "conservador": "Prompt formal...",
    "moderado": "Prompt equilibrado...",
    "liberal": "Prompt casual..."
}
```

---

## Logging

### Configuração

```python
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s | %(levelname)-8s | %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S',
    handlers=[
        RotatingFileHandler(
            'logs/bot.log',
            maxBytes=5*1024*1024,
            backupCount=5,
            encoding='utf-8'
        ),
        logging.StreamHandler()
    ]
)
```

### Logger

```python
logger = logging.getLogger('SamiraBot')
```

### Métodos

#### `logger.info(message)`
Registra evento informativo.

#### `logger.warning(message)`
Registra aviso.

#### `logger.exception(message)`
Registra erro com stack trace completo.
