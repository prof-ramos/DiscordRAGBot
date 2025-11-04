# Guia de Uso

## Modos de Interação

```mermaid
graph TD
    User[👤 Usuário] --> Choice{Como quer<br/>interagir?}
    
    Choice -->|Formal| Slash[/ask comando]
    Choice -->|Casual| Mention[@BotName menção]
    Choice -->|Privado| DM[Mensagem Direta]
    
    Slash --> Process[Bot processa]
    Mention --> Process
    DM --> Process
    
    Process --> RAG[Sistema RAG]
    RAG --> Response[Resposta + Fontes]
    
    Response --> SlashReply[Resposta no canal]
    Response --> MentionReply[Resposta visível para todos]
    Response --> DMReply[Resposta privada]
    
    style User fill:#4CAF50,stroke:#2E7D32,color:#fff
    style Slash fill:#5865F2,stroke:#4752C4,color:#fff
    style Mention fill:#5865F2,stroke:#4752C4,color:#fff
    style DM fill:#5865F2,stroke:#4752C4,color:#fff
    style Response fill:#4CAF50,stroke:#2E7D32,color:#fff
```

O bot suporta 3 formas diferentes de interação:

### 1. Comandos Slash (`/ask`)

Modo mais formal e estruturado.

```
/ask pergunta: Como escrever documentação técnica?
```

**Vantagens**:
- ✅ Autocompletar
- ✅ Validação de parâmetros
- ✅ Interface visual

**Uso**:
1. Digite `/` no chat
2. Selecione `ask` da lista
3. Digite sua pergunta
4. Pressione Enter

### 2. Menções em Canais

Mencione o bot em qualquer canal.

```
@BotName Explique o que é RAG
```

**Vantagens**:
- ✅ Natural e conversacional
- ✅ Visível para todos no canal
- ✅ Contexto compartilhado

**Uso**:
1. Digite `@` e o nome do bot
2. Escreva sua pergunta após a menção
3. Pressione Enter

### 3. Mensagens Diretas (DM)

Conversas privadas com o bot.

```
Olá! Preciso de ajuda com Python
```

**Vantagens**:
- ✅ Privacidade total
- ✅ Sem poluir canais
- ✅ Histórico pessoal

**Uso**:
1. Abra DM com o bot
2. Envie qualquer mensagem
3. O bot responde automaticamente

## Comandos Disponíveis

### `/ask` - Fazer Pergunta

Comando principal para interagir com o RAG.

**Sintaxe**:
```
/ask pergunta: <sua pergunta aqui>
```

**Exemplos**:
```
/ask pergunta: O que é um vector store?
/ask pergunta: Como funciona embeddings?
/ask pergunta: Explique RAG em detalhes
```

**Comportamento**:
1. Bot mostra status "pensando..."
2. Busca documentos relevantes
3. Gera resposta usando LLM
4. Retorna resposta + fontes (se houver)

**Fontes**:
```
📚 Fontes:
1. `manual-de-redacao.pdf`
2. `guia-tecnico.pdf`
3. `documentacao.pdf`
```

---

### `/config` - Configurar Nível

Altera a personalidade do bot (apenas administradores).

**Sintaxe**:
```
/config nivel: <conservador|moderado|liberal>
```

**Níveis Disponíveis**:

#### 🔒 Conservador
- Tom formal e profissional
- Evita linguagem casual
- Respostas verificadas e neutras
- Apropriado para todos os públicos

**Exemplo de resposta**:
> "Prezado usuário, RAG (Retrieval-Augmented Generation) é uma técnica que combina busca vetorial com modelos de linguagem. Permite consultas precisas em documentos indexados."

#### ⚖️ Moderado (Padrão)
- Equilibrado e empático
- Adaptabilidade cognitiva
- Profundidade informacional
- Conexão humana

**Exemplo de resposta**:
> "RAG é uma técnica poderosa que une o melhor de dois mundos: a precisão da busca vetorial e a naturalidade dos LLMs. Pense nisso como dar ao modelo acesso a uma biblioteca específica de conhecimento."

#### 🔓 Liberal
- Casual e descontraído
- Naturalidade e autenticidade
- Expressões coloquiais
- Criatividade

**Exemplo de resposta**:
> "Cara, RAG é massa! Basicamente você dá uma biblioteca pro modelo ler antes de responder. Tipo assim: em vez de chutar, ele pesquisa nos docs e aí responde baseado no que achou. Sacou?"

**Permissões**:
- ⚠️ **Apenas administradores** podem alterar
- Outros usuários recebem: "❌ Apenas administradores podem alterar as configurações do bot!"

**Exemplos**:
```
/config nivel: conservador
/config nivel: moderado
/config nivel: liberal
```

### Sistema de Configuração por Servidor

```mermaid
graph TB
    Admin[👤 Admin] -->|/config nivel: liberal| Bot[🤖 Bot]
    User[👤 Usuário Normal] -->|/config nivel: liberal| Bot
    
    Bot --> CheckPerm{É admin?}
    
    CheckPerm -->|Não| Deny[❌ Acesso Negado]
    CheckPerm -->|Sim| GetGuild[Obter Guild ID]
    
    GetGuild --> Update[Atualizar Config]
    Update --> JSON[(server_config.json)]
    
    JSON --> Save[Salvar]
    Save --> Confirm[✅ Nível alterado<br/>para liberal]
    
    Deny --> UserMsg[Mensagem: Apenas<br/>admins podem alterar]
    Confirm --> AdminMsg[Mensagem: Configuração<br/>atualizada com sucesso]
    
    subgraph "Próxima Pergunta"
        NextQ[/ask pergunta] --> LoadConf[Carregar Config]
        LoadConf --> JSON
        JSON --> GetLevel[Obter Nível]
        GetLevel --> SelectPrompt[Selecionar Prompt]
        SelectPrompt --> Liberal[Prompt Liberal]
        SelectPrompt --> Moderado[Prompt Moderado]
        SelectPrompt --> Conservador[Prompt Conservador]
    end
    
    style Admin fill:#4CAF50,stroke:#2E7D32,color:#fff
    style User fill:#FF9800,stroke:#F57C00,color:#fff
    style Deny fill:#f44336,stroke:#c62828,color:#fff
    style Confirm fill:#4CAF50,stroke:#2E7D32,color:#fff
    style JSON fill:#2196F3,stroke:#1976D2,color:#fff
```

**Como funciona:**

1. Admin executa `/config nivel: liberal`
2. Bot verifica permissões de administrador
3. Se autorizado, atualiza `server_config.json`
4. Todas as próximas perguntas usam o novo nível
5. Usuários não-admin veem mensagem de erro

---

### `/status` - Ver Configurações

Mostra configurações atuais do bot.

**Sintaxe**:
```
/status
```

**Informações Exibidas**:

```
⚙️ Configurações do Bot
Configurações atuais para servidor MeuServidor

Nível de Filtro
⚖️ MODERADO
Equilibrado e empático (padrão)

Modelo LLM                  RAG Status
minimax/minimax-m2:free     ✅ Ativo

Use /config para alterar o nível (apenas admins)
```

**Uso em DM**:
- Mostra "DMs" em vez de nome do servidor
- Configuração individual (não compartilhada)

---

## Exemplos Práticos

### Caso 1: Busca Simples

```
/ask pergunta: O que é Python?
```

**Resposta**:
> Python é uma linguagem de programação de alto nível...
>
> 📚 Fontes:
> 1. `introducao-python.pdf`

### Caso 2: Pergunta Complexa

```
/ask pergunta: Compare RAG com fine-tuning de modelos. Quando usar cada um?
```

**Resposta**:
> RAG e fine-tuning são abordagens complementares...
> [Resposta detalhada com comparação]
>
> 📚 Fontes:
> 1. `ml-best-practices.pdf`
> 2. `llm-techniques.pdf`

### Caso 3: Pergunta Sem Contexto

```
/ask pergunta: Qual é a capital da França?
```

**Resposta**:
> ⚠️ **Informação não encontrada nos documentos**
> Não encontrei informações sobre isso nos documentos indexados.

### Caso 4: Configuração de Servidor

```
# Admin muda nível
/config nivel: liberal

# Qualquer usuário consulta
/status
```

**Resultado**: Todas as respostas do servidor agora usam tom casual.

---

## Boas Práticas

### ✅ Fazer

- **Seja específico**: "Como implementar cache no RAG?" vs "Como melhorar?"
- **Use contexto**: "Explique embeddings no contexto de busca semântica"
- **Perguntas diretas**: Evite ambiguidade
- **Temas dos PDFs**: Pergunte sobre conteúdo indexado

### ❌ Evitar

- **Perguntas genéricas**: "Me ajude" (seja específico)
- **Múltiplas perguntas**: Faça uma por vez
- **Temas não indexados**: Bot não tem conhecimento geral
- **Spam**: Aguarde resposta antes de nova pergunta

---

## Dicas de Uso

### Para Administradores

**Configurar Servidor**:
1. Teste diferentes níveis com `/config`
2. Use `/status` para confirmar mudanças
3. Peça feedback dos membros
4. Ajuste conforme necessário

**Manutenção**:
- Monitore logs em `logs/bot.log`
- Adicione novos PDFs e reindexe quando necessário
- Verifique custos de API mensalmente

### Para Usuários

**Obter Melhores Respostas**:
1. Seja específico na pergunta
2. Use termos presentes nos documentos
3. Leia as fontes fornecidas
4. Faça follow-up se necessário

**Privacidade**:
- Use DM para perguntas sensíveis
- Comandos em canais são visíveis para todos
- Logs registram User ID (não conteúdo sensível)

---

## Workflow Típico

### Usuário Novo

1. **Testar bot**
```
/ask pergunta: Olá, como você funciona?
```

2. **Verificar configuração**
```
/status
```

3. **Fazer pergunta real**
```
/ask pergunta: [sua pergunta sobre os documentos]
```

### Administrador Novo

1. **Verificar status inicial**
```
/status
```

2. **Testar diferentes níveis**
```
/config nivel: conservador
/ask pergunta: Teste
/config nivel: liberal
/ask pergunta: Teste
```

3. **Escolher nível final**
```
/config nivel: moderado
```

---

## Limitações

### O que o Bot PODE fazer

✅ Responder perguntas sobre **documentos indexados**  
✅ Citar **fontes** das respostas  
✅ Ajustar **personalidade** por servidor  
✅ Processar em **português brasileiro**  
✅ Funcionar via **comandos**, **menções** e **DMs**

### O que o Bot NÃO PODE fazer

❌ Conhecimento geral (fora dos PDFs)  
❌ Acesso à internet em tempo real  
❌ Processar imagens ou áudio  
❌ Executar código  
❌ Lembrar conversas anteriores (sem memória)  
❌ Modificar PDFs indexados

---

## Próximos Passos

Agora que você sabe usar o bot:

👉 Consulte [Logs](logs.md) para monitoramento  
👉 Veja [Referência API](api.md) para detalhes técnicos  
👉 Leia [Troubleshooting](troubleshooting.md) se tiver problemas
