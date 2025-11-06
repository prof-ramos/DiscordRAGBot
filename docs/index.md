# Bot Discord RAG PT-BR

## Visão Geral

Bem-vindo à documentação técnica do Bot Discord RAG PT-BR!

### Sumário do Projeto

**Nome**: Bot Discord RAG PT-BR
**Propósito**: Bot Discord com RAG (Retrieval-Augmented Generation) que responde perguntas baseadas em documentos em múltiplos formatos (PDF, DOCX, TXT, CSV, Excel, Markdown), otimizado para português brasileiro.
**Linguagem Principal**: Python 3.11
**Arquitetura**: Sistema RAG (Retrieval-Augmented Generation) com busca vetorial e LLM

### O que é RAG?

RAG (Retrieval-Augmented Generation) é uma técnica que combina:

1. **Recuperação de informações** - Busca vetorial em documentos indexados
2. **Geração de respostas** - LLM (Large Language Model) para criar respostas naturais

```
PDFs → Indexação → Vector Store → Recuperação → LLM → Resposta
```

### Características Principais

✅ **Múltiplas formas de interação**:
- Comando slash `/ask` em servidores
- Menções `@BotName` em canais
- Mensagens diretas (DM)

✅ **Sistema RAG completo**:
- Embeddings multilíngues via OpenAI API (text-embedding-3-small)
- Busca vetorial com Chroma
- Integração com OpenRouter (Claude, GPT, Gemini, Llama, etc.)

✅ **Configuração flexível**:
- 3 níveis de personalidade (conservador, moderado, liberal)
- Configurável por servidor
- Controle de acesso baseado em permissões

✅ **Sistema de logs robusto**:
- Logs rotativos com stack traces completos
- Rastreamento de todas as interações
- Análise detalhada de erros

### Dependências Principais

```python
discord.py          # Framework Discord Bot
langchain           # Orquestração RAG
langchain-openai    # Embeddings e LLM OpenAI
langchain-community # Chroma e loaders
chromadb            # Banco vetorial
python-dotenv       # Variáveis de ambiente
pypdf               # Leitura de PDFs
openai              # API OpenAI
```

### Início Rápido

1. **Instalar dependências**
```bash
pip install -r requirements.txt
```

2. **Configurar variáveis de ambiente** (`.env`)
```bash
DISCORD_TOKEN=seu_token
OPENAI_API_KEY=sua_chave
OPENROUTER_API_KEY=sua_chave
```

3. **Indexar documentos**
```bash
python load.py
```

4. **Iniciar bot**
```bash
python bot.py
```

Consulte as seções de [Instalação](installation.md) e [Uso](usage.md) para detalhes completos.

### Estrutura da Documentação

- **[Arquitetura](architecture.md)** - Componentes e design do sistema
- **[Instalação](installation.md)** - Setup completo passo a passo
- **[Uso](usage.md)** - Guia de uso e comandos
- **[Formatos Suportados](formatos_suportados.md)** - Documentos suportados e como usá-los
- **[Logs](logs.md)** - Sistema de logging e análise
- **[Referência API](api.md)** - Funções e classes detalhadas
- **[Troubleshooting](troubleshooting.md)** - Solução de problemas comuns

### Próximos Passos

👉 Continue para [Arquitetura](architecture.md) para entender o design do sistema  
👉 Ou vá direto para [Instalação](installation.md) para começar a usar
