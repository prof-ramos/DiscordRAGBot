# Sistema de Logs

## Visão Geral

O bot possui um sistema completo de logging que registra **todas as atividades** de forma organizada e profissional.

## Configuração

### Localização dos Logs

- **Arquivo principal**: `logs/bot.log`
- **Backups**: `bot.log.1`, `bot.log.2`, etc.
- **Rotação automática**: 5 MB por arquivo
- **Quantidade de backups**: Últimos 5 arquivos
- **Encoding**: UTF-8 (suporte completo a caracteres especiais)

### Formato de Log

```
timestamp | nível | mensagem
```

**Exemplo**:
```
2025-11-03 00:06:32 | INFO     | 🔄 Iniciando carregamento do RAG...
2025-11-03 00:06:33 | INFO     | ✅ RAG carregado | Modelo: minimax/minimax-m2:free
```

### Níveis de Log

| Nível | Uso | Exemplo |
|-------|-----|---------|
| **INFO** | Eventos normais | Bot iniciado, comando executado |
| **WARNING** | Avisos não críticos | RAG não carregado, acesso negado |
| **ERROR** | Erros com stack trace | Exceções, falhas de API |

## Eventos Registrados

### 1. Inicialização

Eventos durante startup do bot:

```
2025-11-03 00:06:32 | WARNING  | PyNaCl is not installed, voice will NOT be supported
2025-11-03 00:06:32 | INFO     | 🔄 Iniciando carregamento do RAG...
2025-11-03 00:06:33 | INFO     | ✅ RAG carregado | Modelo: minimax/minimax-m2:free | K_DOCS: 5
2025-11-03 00:06:33 | INFO     | logging in using static token
2025-11-03 00:06:34 | INFO     | Shard ID None has connected to Gateway
2025-11-03 00:06:36 | INFO     | 🤖 Bot iniciado | Nome: BotName#1234 | Servidores: 1
2025-11-03 00:06:36 | INFO     | ⚙️ Comandos sincronizados | Total: 3
```

**Informações capturadas**:
- ✅ Status do carregamento do RAG
- ✅ Modelo LLM configurado
- ✅ Número de documentos recuperados (K_DOCS)
- ✅ Nome do bot
- ✅ Quantidade de servidores
- ✅ Comandos sincronizados

### 2. Interações com Usuários

Todas as interações são registradas:

#### Comando `/ask`
```
2025-11-03 00:10:45 | INFO     | 🔹 Comando /ask | Servidor: 123456789 | Usuário: 987654321
2025-11-03 00:10:45 | INFO     | 💬 CMD /ask | Servidor: 123456789 | Usuário: 987654321 | Nível: moderado | Pergunta: Como funciona RAG...
2025-11-03 00:10:48 | INFO     | ✅ Resposta enviada | Servidor: 123456789 | Usuário: 987654321 | Fontes: 3
```

#### Menção em Canal
```
2025-11-03 00:15:20 | INFO     | 📩 Menção | Servidor: 123456789 | Usuário: 444555666
2025-11-03 00:15:20 | INFO     | 💬 Menção | Servidor: 123456789 | Usuário: 444555666 | Nível: liberal | Pergunta: Explique embeddings...
2025-11-03 00:15:23 | INFO     | ✅ Resposta enviada | Servidor: 123456789 | Usuário: 444555666 | Fontes: 2
```

#### Mensagem Direta (DM)
```
2025-11-03 00:20:10 | INFO     | 📨 DM recebida | Usuário: 111222333
2025-11-03 00:20:10 | INFO     | 💬 DM | Servidor: DM | Usuário: 111222333 | Nível: moderado | Pergunta: O que é Chroma...
2025-11-03 00:20:13 | INFO     | ✅ Resposta enviada | Servidor: DM | Usuário: 111222333 | Fontes: 4
```

**Informações capturadas**:
- User ID (identificador único)
- Guild ID / Servidor (ou "DM")
- Tipo de interação (CMD /ask, Menção, DM)
- Nível de filtro aplicado
- Preview da pergunta (primeiros 50 caracteres)
- Número de fontes retornadas

### 3. Comandos de Configuração

#### `/config` - Sucesso
```
2025-11-03 00:25:30 | INFO     | 🔹 Comando /config | Servidor: 123456789 | Usuário: 777888999 | Tentativa: liberal
2025-11-03 00:25:30 | INFO     | 📝 Configuração alterada | Servidor: 123456789 | Novo nível: liberal
```

#### `/config` - Acesso Negado
```
2025-11-03 00:30:15 | INFO     | 🔹 Comando /config | Servidor: 123456789 | Usuário: 555666777 | Tentativa: conservador
2025-11-03 00:30:15 | WARNING  | ⚠️ Acesso negado /config | Servidor: 123456789 | Usuário: 555666777 (não admin)
```

#### `/status`
```
2025-11-03 00:35:40 | INFO     | 🔹 Comando /status | Servidor: 123456789 | Usuário: 888999000
```

**Informações capturadas**:
- Tentativas de configuração (todas)
- Sucesso ou negação de acesso
- Novo nível configurado
- User ID do solicitante

### 4. Erros e Exceções

#### RAG Não Carregado
```
2025-11-03 00:40:50 | WARNING  | ⚠️ RAG não carregado | Usuário: 222333444 | Servidor: None
```

#### Erro ao Processar Pergunta
```
2025-11-03 00:45:20 | ERROR    | ❌ Erro ao processar | Servidor: DM | Usuário: 333444555 | Erro: Connection timeout
Traceback (most recent call last):
  File "bot.py", line 205, in processar_pergunta
    result = qa_chain.invoke({"input": question})
  ...
  ConnectionError: Connection timeout after 30s
```

#### Erro de Sincronização
```
2025-11-03 00:50:10 | ERROR    | ❌ Erro ao sincronizar comandos | Erro: HTTPException
Traceback (most recent call last):
  File "bot.py", line 240, in on_ready
    synced = await bot.tree.sync()
  ...
  discord.errors.HTTPException: 429 Too Many Requests
```

**Informações capturadas**:
- ⚠️ Warnings para problemas não críticos
- ❌ Errors com stack traces completos
- Contexto completo (usuário, servidor, ação)

## Análise de Logs

### Comandos Úteis

#### Ver logs em tempo real
```bash
tail -f logs/bot.log
```

#### Buscar erros
```bash
grep "ERROR" logs/bot.log
grep "EXCEPTION" logs/bot.log
```

#### Buscar atividade de usuário específico
```bash
grep "Usuário: 123456789" logs/bot.log
```

#### Buscar por servidor
```bash
grep "Servidor: 987654321" logs/bot.log
```

#### Filtrar por tipo de interação
```bash
grep "CMD /ask" logs/bot.log      # Comandos slash
grep "Menção" logs/bot.log        # Menções
grep "DM" logs/bot.log            # Mensagens diretas
```

#### Ver últimas N linhas
```bash
tail -n 50 logs/bot.log   # Últimas 50 linhas
tail -n 100 logs/bot.log  # Últimas 100 linhas
```

#### Contar eventos
```bash
# Quantas perguntas foram feitas?
grep "💬" logs/bot.log | wc -l

# Quantos erros ocorreram?
grep "ERROR" logs/bot.log | wc -l

# Quantas configurações foram alteradas?
grep "📝 Configuração alterada" logs/bot.log | wc -l
```

#### Análise temporal
```bash
# Atividade de hoje
grep "2025-11-03" logs/bot.log

# Atividade de uma hora específica
grep "2025-11-03 14:" logs/bot.log
```

### Exemplos de Análise

#### Encontrar usuários mais ativos
```bash
grep "Usuário:" logs/bot.log | awk '{print $9}' | sort | uniq -c | sort -nr | head -10
```

#### Análise de erros por tipo
```bash
grep "ERROR" logs/bot.log | awk -F'|' '{print $3}' | sort | uniq -c | sort -nr
```

#### Servidores com mais atividade
```bash
grep "Servidor:" logs/bot.log | grep -v "DM" | awk '{print $7}' | sort | uniq -c | sort -nr
```

## Monitoramento

### Indicadores de Saúde

**Bot Saudável**:
```
✅ Sem mensagens ERROR recentes
✅ RAG carregado com sucesso
✅ Comandos sincronizados
✅ Respostas sendo enviadas
```

**Bot com Problemas**:
```
❌ Múltiplas mensagens ERROR
❌ RAG não carregado
❌ Erros de sincronização
❌ Timeouts frequentes
```

### Alertas Importantes

| Mensagem | Severidade | Ação |
|----------|------------|------|
| `RAG não carregado` | ⚠️ Alta | Executar `python load.py` |
| `Erro ao sincronizar comandos` | ⚠️ Média | Verificar conexão Discord |
| `Connection timeout` | ⚠️ Média | Verificar OpenRouter/OpenAI |
| `Acesso negado /config` | ✅ Baixa | Normal (usuário não-admin) |

## Rotação de Logs

### Como Funciona

O sistema usa `RotatingFileHandler`:

1. **Arquivo principal**: `bot.log` (ativo)
2. **Quando atinge 5MB**: Renomeia para `bot.log.1`
3. **Logs existentes**: Renomeados sequencialmente
   - `bot.log.1` → `bot.log.2`
   - `bot.log.2` → `bot.log.3`
   - etc.
4. **Limite**: Mantém últimos 5 backups
5. **Mais antigo**: `bot.log.5` é deletado

### Estrutura de Arquivos

```
logs/
├── bot.log       # Arquivo ativo (atual)
├── bot.log.1     # Backup 1 (mais recente)
├── bot.log.2     # Backup 2
├── bot.log.3     # Backup 3
├── bot.log.4     # Backup 4
└── bot.log.5     # Backup 5 (mais antigo)
```

### Verificar Tamanho

```bash
ls -lh logs/
```

Output:
```
-rw-r--r-- 1 user user 3.2M Nov  3 10:00 bot.log
-rw-r--r-- 1 user user 5.0M Nov  3 09:00 bot.log.1
-rw-r--r-- 1 user user 5.0M Nov  3 08:00 bot.log.2
```

## Boas Práticas

### ✅ Fazer

- **Monitorar regularmente**: `tail -f logs/bot.log`
- **Buscar erros diariamente**: `grep "ERROR" logs/bot.log`
- **Arquivar logs antigos**: Copiar backups importantes
- **Analisar padrões**: Identificar horários de pico

### ❌ Evitar

- **Deletar logs ativos**: Pode causar erros
- **Compartilhar logs**: Contêm User IDs e Guild IDs
- **Ignorar WARNING**: Podem indicar problemas futuros
- **Desabilitar logs**: Essenciais para debugging

## Privacidade e Segurança

### O que é Registrado

✅ User ID (numérico, não identificável)  
✅ Guild ID (numérico, não identificável)  
✅ Tipo de interação  
✅ Nível de filtro  
✅ Preview da pergunta (50 chars)  
✅ Número de fontes

### O que NÃO é Registrado

❌ Conteúdo completo das perguntas  
❌ Respostas do bot  
❌ Nomes de usuários  
❌ Nomes de servidores  
❌ Tokens ou API keys  
❌ Conteúdo dos PDFs

## Troubleshooting de Logs

### Logs não aparecem

**Problema**: Arquivo `bot.log` não existe

**Solução**:
```bash
mkdir -p logs
python bot.py  # Cria automaticamente
```

### Logs muito grandes

**Problema**: Arquivos `bot.log` excedendo 5MB

**Solução**: A rotação é automática. Se persistir:
```bash
# Forçar rotação manual
mv logs/bot.log logs/bot.log.backup
touch logs/bot.log
```

### Encoding incorreto

**Problema**: Caracteres estranhos nos logs

**Solução**: Logs usam UTF-8. Visualize com:
```bash
less -r logs/bot.log
cat logs/bot.log | iconv -f UTF-8
```

## Próximos Passos

👉 Veja [Referência API](api.md) para entender funções de logging  
👉 Consulte [Troubleshooting](troubleshooting.md) para resolver problemas
