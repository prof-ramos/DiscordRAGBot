# 🤖 Bot Discord RAG PT-BR com OpenRouter e Supabase

Bot Discord com RAG (Retrieval-Augmented Generation) otimizado para português, utilizando Supabase com pgvector para busca vetorial, embeddings da OpenAI e OpenRouter para acesso a modelos LLM.

## 📋 Funcionalidades

- **Múltiplas formas de interação:**
  - Comando slash `/ask` em servidores
  - Menções `@BotName` em canais
  - Mensagens diretas (DM)
  
- **RAG Pipeline:**
  - Embeddings multilíngues via OpenAI API (text-embedding-3-small)
  - Busca vetorial com Supabase vectorstore (pgvector)
  - Integração com OpenRouter (Claude, GPT, Gemini, Llama, etc.)
  
- **Recursos:**
  - Respostas com citação de fontes
  - Divisão automática de mensagens longas
  - Suporte a PDFs
  - Configuração de níveis de filtro de conteúdo (conservador, moderado, liberal)

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

### 5. Configurar Supabase

1. Crie uma conta em [Supabase](https://supabase.com/)
2. Crie um novo projeto
3. No painel do projeto, anote:
   - **Project URL** (ex: https://seuprojeto.supabase.co)
   - **Project API Key** (seção Settings → API)

4. Configure o banco de dados para vetores:
   - Acesse o painel SQL do Supabase
   - Execute: `CREATE EXTENSION IF NOT EXISTS vector;`
   - Execute o script de criação da tabela (veja docs/supabase_setup.md)

### 6. Configurar Variáveis de Ambiente

Adicione as seguintes chaves no arquivo `.env`:

```bash
DISCORD_TOKEN=seu_token_aqui
OPENAI_API_KEY=sua_chave_openai_aqui
OPENROUTER_API_KEY=sua_chave_openrouter_aqui
OPENROUTER_MODEL=minimax/minimax-m2:free
SUPABASE_URL=sua_url_supabase_aqui
SUPABASE_API_KEY=sua_chave_supabase_aqui
#OPENROUTER_MODEL_FALLBACK=anthropic/claude-3-haiku  # Opcional
```

**Modelos disponíveis no OpenRouter:**
- `minimax/minimax-m2:free` ⭐ **GRATUITO** (padrão recomendado)
- `anthropic/claude-3.5-sonnet` (melhor qualidade, pago)
- `anthropic/claude-3-haiku` (balanceado, econômico)
- `google/gemini-flash-1.5` (rápido e barato)
- `meta-llama/llama-3.1-70b-instruct` (alternativa open source)

## 📦 Instalação

```bash
# Clonar repositório
git clone seu_repositorio
cd DiscordRAGBot

# Criar ambiente virtual
python -m venv venv
source venv/bin/activate  # No Windows: venv\Scripts\activate

# Instalar dependências
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
- Salvar embeddings no vectorstore do Supabase

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
├── data/                  # PDFs para indexar (adicione seus arquivos aqui)
├── logs/                  # Logs do bot (gerado automaticamente)
│   └── bot.log            # Arquivo principal de logs com rotação
├── docs/                  # Documentação adicional
│   └── supabase_setup.md  # Configuração do vectorstore no Supabase
├── load.py                # Script de indexação de documentos
├── bot.py                 # Bot Discord com RAG
├── requirements.txt       # Dependências Python
├── .env.example           # Template de configuração
├── .gitignore             # Arquivos ignorados pelo git
└── README.md              # Este arquivo
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

## 🗄️ Configuração do Supabase Vectorstore

Para usar o Supabase como vectorstore, siga os passos no arquivo `docs/supabase_setup.md`:

1. Habilite a extensão `pgvector`
2. Crie a tabela `documents` com colunas apropriadas para embeddings
3. Crie a função `match_documents` para busca vetorial

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
- 🗃️ **Importante**: Não use em produção sem medidas de segurança adicionais
- 🔐 Use tokens com escopo limitado e prazo de validade

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
