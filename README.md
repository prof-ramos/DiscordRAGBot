# 🤖 Bot Discord RAG PT-BR com OpenRouter

Bot Discord com RAG (Retrieval-Augmented Generation) otimizado para português, utilizando Chroma para busca vetorial, embeddings da OpenAI e OpenRouter para acesso a modelos LLM.

## 📋 Funcionalidades

- **Múltiplas formas de interação:**
  - Comando slash `/ask` em servidores
  - Menções `@BotName` em canais
  - Mensagens diretas (DM)
  
- **RAG Pipeline:**
  - Embeddings multilíngues via OpenAI API (text-embedding-3-small)
  - Busca vetorial com Chroma
  - Integração com OpenRouter (Claude, GPT, Gemini, Llama, etc.)
  
- **Recursos:**
  - Respostas com citação de fontes
  - Divisão automática de mensagens longas
  - Suporte a PDFs

## 🚀 Configuração

### 1. Criar Bot no Discord

1. Acesse [Discord Developer Portal](https://discord.com/developers/applications)
2. Clique em **New Application** e dê um nome ao bot
3. Vá em **Bot** → **Add Bot**
4. Copie o **Token** (você vai precisar dele)
5. Em **Privileged Gateway Intents**, ative:
   - ✅ MESSAGE CONTENT INTENT
   - ✅ SERVER MEMBERS INTENT (opcional)

### 2. Gerar URL de Convite

1. Vá em **OAuth2** → **URL Generator**
2. Em **Scopes**, selecione:
   - ✅ `bot`
   - ✅ `applications.commands`
3. Em **Bot Permissions**, selecione:
   - ✅ Send Messages
   - ✅ Read Message History
   - ✅ Use Slash Commands
4. Copie a URL gerada e adicione o bot ao seu servidor

### 3. Configurar OpenAI (para embeddings)

1. Crie uma conta em [OpenAI Platform](https://platform.openai.com/)
2. Vá em **API Keys** e crie uma nova chave
3. Copie sua chave API
4. Nota: Embeddings têm custo baixo (~$0.02 por 1M tokens)

### 4. Configurar OpenRouter (para respostas LLM)

1. Crie uma conta em [OpenRouter](https://openrouter.ai/)
2. Vá em **Settings** → **API Keys** → **Create Key**
3. Copie sua chave API

### 5. Configurar Variáveis de Ambiente

Adicione as seguintes chaves na aba "Secrets" do Replit:

```bash
DISCORD_TOKEN=seu_token_aqui
OPENAI_API_KEY=sua_chave_openai_aqui
OPENROUTER_API_KEY=sua_chave_openrouter_aqui
OPENROUTER_MODEL=minimax/minimax-m2:free
#OPENROUTER_MODEL_FALLBACK=anthropic/claude-3-haiku  # Opcional
```

**Modelos disponíveis no OpenRouter:**
- `minimax/minimax-m2:free` ⭐ **GRATUITO** (padrão recomendado)
- `anthropic/claude-3.5-sonnet` (melhor qualidade, pago)
- `anthropic/claude-3-haiku` (balanceado, econômico)
- `google/gemini-flash-1.5` (rápido e barato)
- `meta-llama/llama-3.1-70b-instruct` (alternativa open source)

## 📦 Instalação

As dependências já estão instaladas no Replit. Se precisar reinstalar:

```bash
pip install -r requirements.txt
```

## 📚 Indexar Documentos

### 1. Adicionar PDFs

Coloque seus arquivos PDF na pasta `data/`:

```
data/
├── documento1.pdf
├── documento2.pdf
└── documento3.pdf
```

### 2. Executar indexação

```bash
python load.py
```

Isso irá:
- Carregar todos os PDFs da pasta `data/`
- Dividir em chunks otimizados
- Criar embeddings via OpenAI API (text-embedding-3-small)
- Salvar banco vetorial Chroma em `vectorstore/`

## 🤖 Executar o Bot

```bash
python bot.py
```

Você verá:
```
[INFO] Carregando RAG...
[✅] RAG carregado com sucesso.
[✅] Bot conectado como SeuBot#1234
[✅] 1 comandos sincronizados
```

## 💬 Como Usar

### Comando Slash
```
/ask pergunta: Qual a capital do Brasil?
```

### Menção no Servidor
```
@BotName O que é LGPD?
```

### Mensagem Direta
```
Envie qualquer mensagem direta ao bot
```

## 🔧 Estrutura do Projeto

```
.
├── data/              # PDFs para indexar (adicione seus arquivos aqui)
├── vectorstore/       # Banco vetorial Chroma (gerado automaticamente)
├── logs/              # Logs do bot (gerado automaticamente)
│   └── bot.log        # Arquivo principal de logs com rotação
├── load.py            # Script de indexação de documentos
├── bot.py             # Bot Discord com RAG
├── requirements.txt   # Dependências Python
├── .env.example       # Template de configuração
├── .gitignore         # Arquivos ignorados pelo git
├── README.md          # Este arquivo
└── replit.md          # Documentação técnica do projeto
```

## 📊 Sistema de Logs

O bot possui um sistema completo de logs que registra todas as atividades:

### Localização dos Logs
- **Arquivo principal:** `logs/bot.log`
- **Rotação automática:** Máximo 5 MB por arquivo, mantém últimos 5 backups
- **Encoding:** UTF-8 (suporte a caracteres especiais)

### Informações Registradas

**Inicialização:**
```
2025-11-03 00:03:14 | INFO     | 🔄 Iniciando carregamento do RAG...
2025-11-03 00:03:15 | INFO     | ✅ RAG carregado | Modelo: minimax/minimax-m2:free | K_DOCS: 5
2025-11-03 00:03:19 | INFO     | 🤖 Bot iniciado | Nome: BotName#1234 | Servidores: 2
2025-11-03 00:03:20 | INFO     | ⚙️ Comandos sincronizados | Total: 3
```

**Interações do usuário:**
```
2025-11-03 00:05:32 | INFO     | 🔹 Comando /ask | Servidor: 123456789 | Usuário: 987654321
2025-11-03 00:05:32 | INFO     | 💬 CMD /ask | Servidor: 123456789 | Usuário: 987654321 | Nível: moderado | Pergunta: Como fazer...
2025-11-03 00:05:35 | INFO     | ✅ Resposta enviada | Servidor: 123456789 | Usuário: 987654321 | Fontes: 3
```

**Configurações:**
```
2025-11-03 00:10:15 | INFO     | 🔹 Comando /config | Servidor: 123456789 | Usuário: 111222333 | Tentativa: liberal
2025-11-03 00:10:15 | INFO     | 📝 Configuração alterada | Servidor: 123456789 | Novo nível: liberal
```

**Erros:**
```
2025-11-03 00:15:20 | ERROR    | ❌ Erro ao processar | Servidor: DM | Usuário: 444555666 | Erro: Connection timeout
2025-11-03 00:16:30 | WARNING  | ⚠️ RAG não carregado | Usuário: 777888999 | Servidor: None
```

### Tipos de Eventos Registrados
- ✅ Inicialização do bot e carregamento do RAG
- 💬 Todas as perguntas processadas (comando, menção, DM)
- 📝 Mudanças de configuração (nível de filtro)
- 🔹 Uso de comandos slash (/ask, /config, /status)
- ⚠️ Tentativas de acesso não autorizado
- ❌ Erros e exceções com stack traces completos

### Analisar Logs

```bash
# Ver logs em tempo real
tail -f logs/bot.log

# Buscar erros
grep "ERROR" logs/bot.log

# Buscar atividade de um usuário específico
grep "Usuário: 123456789" logs/bot.log

# Ver últimas 50 linhas
tail -n 50 logs/bot.log
```

## ⚡ Otimizações

Para reduzir custos e melhorar performance:

```python
# Reduzir número de documentos recuperados (em bot.py)
K_DOCS = 3  # Mudar de 5 para 3

# Reduzir tokens máximos (em bot.py)
model_kwargs={"max_tokens": 500}  # Mudar de 1000 para 500

# Usar modelo mais barato no OpenRouter
OPENROUTER_MODEL=anthropic/claude-3-haiku  # Mais barato que sonnet
```

## 🛡️ Segurança

- ⚠️ **Nunca** commite o arquivo `.env` (já está no `.gitignore`)
- 🔒 Mantenha seus tokens e chaves API em segredo
- 🔄 Regenere tokens se forem expostos acidentalmente

## 📝 Próximos Recursos

- [ ] Rate limiting para evitar spam
- [ ] Comandos admin (recarregar banco vetorial, estatísticas)
- [ ] Sistema de feedback com reações (👍/👎)
- [ ] Suporte a outros formatos (DOCX, TXT, Markdown)
- [ ] Dashboard web para visualização de métricas de uso

## 📄 Licença

Este projeto é de código aberto. Use livremente!

## 🤝 Contribuições

Contribuições são bem-vindas! Sinta-se à vontade para abrir issues ou pull requests.
