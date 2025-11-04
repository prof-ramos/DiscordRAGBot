# Discord RAG Bot PT-BR - Replit Project

## 📌 Overview

Bot Discord com RAG (Retrieval-Augmented Generation) otimizado para português. Utiliza Chroma para busca vetorial eficiente, embeddings da OpenAI e OpenRouter para acesso a diversos modelos LLM (Claude, GPT, Gemini, etc.).

## 🎯 Purpose & Goals

Criar um bot Discord que responde perguntas baseadas em documentos PDF fornecidos pelo usuário, utilizando:
- **Embeddings multilíngues** via OpenAI API otimizados para português
- **Chroma** para busca vetorial de alta performance
- **OpenRouter** para flexibilidade de escolha de LLM

## 🏗️ Architecture

### Components

1. **load.py**: Script de indexação de documentos
   - Carrega PDFs da pasta `data/`
   - Cria embeddings usando OpenAI API (text-embedding-3-small)
   - Gera banco vetorial Chroma e salva em `vectorstore/`

2. **bot.py**: Bot Discord com RAG
   - Carrega banco vetorial Chroma
   - Integra com OpenRouter para geração de respostas
   - Usa LangChain 1.0 com create_retrieval_chain
   - Suporta 3 modos de interação: slash commands, mentions, DMs
   - Mensagens e prompts em português brasileiro

### Technology Stack

- **Python 3.11**
- **discord.py**: Framework para bot Discord
- **LangChain 1.0**: Orquestração do pipeline RAG
- **Chroma**: Banco de dados vetorial
- **OpenAI Embeddings API**: Embeddings multilíngues (text-embedding-3-small)
- **OpenRouter**: Gateway para múltiplos LLMs (Claude, GPT, Gemini, etc.)

## 📂 Project Structure

```
.
├── data/              # PDFs para indexação (adicionar manualmente)
├── vectorstore/       # Banco vetorial Chroma (gerado por load.py)
├── logs/              # Logs do bot com rotação automática
│   └── bot.log        # Log principal (max 5MB, 5 backups)
├── load.py            # Indexação de documentos
├── bot.py             # Bot Discord
├── requirements.txt   # Dependências Python
├── server_config.json # Configurações por servidor (níveis de filtro)
├── .env               # Variáveis de ambiente (não versionado)
├── .env.example       # Template
├── .gitignore         # Arquivos ignorados
├── README.md          # Documentação principal
└── replit.md          # Este arquivo
```

## 🔑 Configuration

### Required Environment Variables

- `DISCORD_TOKEN`: Token do bot (Discord Developer Portal)
- `OPENAI_API_KEY`: Chave API do OpenAI (para embeddings)
- `OPENROUTER_API_KEY`: Chave API do OpenRouter (para LLM)
- `OPENROUTER_MODEL`: Modelo LLM a usar (padrão: `anthropic/claude-3.5-sonnet`)

### Setup Instructions

1. **Discord Bot:**
   - Criar aplicação em https://discord.com/developers/applications
   - Ativar "MESSAGE CONTENT INTENT" em Privileged Gateway Intents
   - Copiar token do bot

2. **OpenRouter:**
   - Criar conta em https://openrouter.ai/
   - Gerar API key em Settings → API Keys

3. **Adicionar variáveis de ambiente no Replit:**
   - Usar a aba "Secrets" ou arquivo `.env`

## 🚀 Workflow

### Indexação de Documentos
```bash
python load.py
```
- Processa PDFs em `data/`
- Gera embeddings via OpenAI API
- Salva banco vetorial Chroma

### Executar Bot
```bash
python bot.py
```
- Carrega banco vetorial Chroma
- Conecta ao Discord
- Sincroniza comandos slash
- Fica online aguardando interações

## 📊 Recent Changes

### 2025-11-03: Sistema de Logs Completo
- **Implementado sistema de logging abrangente**:
  - RotatingFileHandler com rotação automática (5MB max, 5 backups)
  - Logs salvos em `logs/bot.log` com encoding UTF-8
  - Formato estruturado: `timestamp | nível | mensagem`
  
- **Eventos registrados**:
  - Inicialização do bot e carregamento do RAG
  - Todas as interações: comandos `/ask`, menções, DMs
  - Mudanças de configuração (níveis de filtro)
  - Tentativas de acesso não autorizado ao `/config`
  - Erros e exceções com stack traces completos
  
- **Informações capturadas**:
  - User ID e Guild ID em cada interação
  - Tipo de interação (CMD /ask, Menção, DM)
  - Nível de filtro aplicado
  - Preview da pergunta (50 primeiros caracteres)
  - Número de fontes retornadas
  - Mensagens de erro detalhadas

### 2025-11-02: Sistema de Filtros de Conteúdo
- Implementado 3 níveis de personalidade configuráveis
- Comandos `/config` e `/status` para gerenciar filtros
- Configurações persistentes por servidor em `server_config.json`
- Controle de acesso: apenas admins podem alterar configurações

### 2025-11-01: Modelo Gratuito e Indexação
- Migrado para modelo gratuito `minimax/minimax-m2:free`
- Indexado Manual de Redação (189 páginas, 540 chunks)
- Adicionado pypdf ao requirements.txt

### 2025-10-30: Initial Setup
- Criado estrutura base do projeto
- Implementado load.py com suporte a PDFs e OpenAI embeddings
- Implementado bot.py com 3 modos de interação
- Migrado para LangChain 1.0 (create_retrieval_chain)
- Substituído FAISS local por Chroma (menor uso de disco)
- Substituído sentence-transformers local por OpenAI Embeddings API (evita quota de disco)
- Prompts e mensagens configurados para português brasileiro
- Workflow configurado para console output

## 💡 User Preferences

*Nenhuma preferência específica registrada ainda.*

## 🔧 Technical Notes

### Disk Space Solution

**Problema resolvido**: Em vez de usar dependências ML pesadas (torch, sentence-transformers, faiss-cpu ~2-3GB), o projeto usa:

- **OpenAI Embeddings API** (text-embedding-3-small) - sem instalação local
- **Chroma** em vez de FAISS - mais leve e fácil de usar
- **LangChain 1.0** - arquitetura modular e moderna

Isso reduz significativamente o uso de disco e torna o projeto viável no Replit.

### Custos

- **OpenAI Embeddings**: ~$0.02 por 1M tokens (muito baixo para uso normal)
- **OpenRouter**: Varia por modelo escolhido
  - Claude 3.5 Sonnet: ~$3/M tokens input
  - Claude 3 Haiku: ~$0.25/M tokens input (mais barato)
  - Gemini Flash: Ainda mais econômico

### Performance Optimization

Para ambientes com RAM limitada:
- Reduzir `batch_size` de 8 para 4
- Reduzir `K_DOCS` de 5 para 3
- Reduzir `max_tokens` de 1000 para 500

## 🐛 Known Issues

- Bot requer que vectorstore já exista antes de iniciar
- Se vectorstore não existir, bot inicia mas retorna mensagem de erro ao receber perguntas
- Usuário deve executar `python load.py` primeiro com PDFs na pasta `data/`

## 📝 Next Steps

- [x] Dependências instaladas
- [x] Bot configurado e rodando
- [x] Sistema de embeddings com OpenAI API
- [x] Workflow configurado
- [x] Sistema de logs completo implementado
- [x] Filtros de conteúdo configuráveis por servidor
- [x] Manual de Redação indexado (540 chunks)
- [ ] Adicionar rate limiting (opcional)
- [ ] Implementar comandos admin (opcional)
- [ ] Dashboard web para visualização de métricas (opcional)

## 🔗 Resources

- [Discord.py Docs](https://discordpy.readthedocs.io/)
- [LangChain Docs](https://python.langchain.com/)
- [OpenRouter](https://openrouter.ai/)
- [Chroma](https://www.trychroma.com/)
- [OpenAI Embeddings](https://platform.openai.com/docs/guides/embeddings)
