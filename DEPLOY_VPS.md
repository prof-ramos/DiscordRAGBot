# 🚀 Deploy Discord RAG Bot em VPS com Portainer e Traefik

Manual completo para deploy do Discord RAG Bot em VPS com Portainer e Traefik já instalados.

## 📋 Pré-requisitos

### ✅ Já Instalado na VPS
- Docker
- Docker Compose
- Portainer
- Traefik (reverse proxy)

### 🔑 Você Precisa Ter
- Acesso SSH à VPS
- Domínio configurado (exemplo: `bot.seudominio.com`)
- Credenciais do Discord Bot
- Chaves API (OpenAI, OpenRouter, Supabase)

---

## 🏗️ Arquitetura do Deploy

```
                    Internet
                       │
                       ▼
                   [Traefik]
                 (reverse proxy)
                       │
          ┌────────────┼────────────┐
          │                         │
          ▼                         ▼
   [Bot Container]          [API Container]
   (Discord Bot)            (Web Interface)
   Port: interno            Port: interno
          │                         │
          └────────────┬────────────┘
                       │
                       ▼
                [Supabase Cloud]
              (Vector Database)
```

---

## 📦 Estrutura de Arquivos no Servidor

```
/opt/discord-rag-bot/
├── docker-compose.yml          # Orquestração dos containers
├── .env                        # Variáveis de ambiente (SEGREDO!)
├── data/                       # Documentos para indexação
│   └── *.pdf, *.docx, etc.
├── logs/                       # Logs do bot (gerado automaticamente)
└── web/                        # Interface web (copiada do repo)
```

---

## 🔧 Passo 1: Preparar o Servidor

### 1.1 Conectar via SSH

```bash
ssh usuario@seu-servidor.com
```

### 1.2 Criar Diretório do Projeto

```bash
sudo mkdir -p /opt/discord-rag-bot
sudo chown $USER:$USER /opt/discord-rag-bot
cd /opt/discord-rag-bot
```

### 1.3 Criar Estrutura de Diretórios

```bash
mkdir -p data logs web/{css,js,assets}
```

---

## 📝 Passo 2: Criar Arquivos de Configuração

### 2.1 Criar `docker-compose.yml`

```bash
nano docker-compose.yml
```

Cole o seguinte conteúdo:

```yaml
version: '3.8'

services:
  # Discord Bot Service
  discord-bot:
    image: python:3.11-slim
    container_name: discord-rag-bot
    restart: unless-stopped
    working_dir: /app
    environment:
      - DISCORD_TOKEN=${DISCORD_TOKEN}
      - OPENAI_API_KEY=${OPENAI_API_KEY}
      - OPENROUTER_API_KEY=${OPENROUTER_API_KEY}
      - OPENROUTER_MODEL=${OPENROUTER_MODEL:-minimax/minimax-m2:free}
      - SUPABASE_URL=${SUPABASE_URL}
      - SUPABASE_API_KEY=${SUPABASE_API_KEY}
      - LOG_LEVEL=${LOG_LEVEL:-INFO}
      - CACHE_ENABLED=${CACHE_ENABLED:-true}
    volumes:
      - ./src:/app/src
      - ./bot.py:/app/bot.py
      - ./logs:/app/logs
      - ./data:/app/data
    command: >
      sh -c "
        pip install --no-cache-dir -q -r /app/requirements.txt &&
        python -u bot.py
      "
    networks:
      - traefik-public
    labels:
      - "com.centurylinklabs.watchtower.enable=true"

  # Web API Service
  api-server:
    image: python:3.11-slim
    container_name: discord-rag-api
    restart: unless-stopped
    working_dir: /app
    environment:
      - DISCORD_TOKEN=${DISCORD_TOKEN}
      - OPENAI_API_KEY=${OPENAI_API_KEY}
      - OPENROUTER_API_KEY=${OPENROUTER_API_KEY}
      - OPENROUTER_MODEL=${OPENROUTER_MODEL:-minimax/minimax-m2:free}
      - SUPABASE_URL=${SUPABASE_URL}
      - SUPABASE_API_KEY=${SUPABASE_API_KEY}
      - LOG_LEVEL=${LOG_LEVEL:-INFO}
      - CACHE_ENABLED=${CACHE_ENABLED:-true}
    volumes:
      - ./src:/app/src
      - ./api_server.py:/app/api_server.py
      - ./web:/app/web
      - ./logs:/app/logs
      - ./data:/app/data
    command: >
      sh -c "
        pip install --no-cache-dir -q -r /app/requirements.txt &&
        python -u api_server.py
      "
    networks:
      - traefik-public
    labels:
      # Traefik labels para roteamento
      - "traefik.enable=true"
      - "traefik.http.routers.discord-rag-api.rule=Host(`bot.seudominio.com`)"
      - "traefik.http.routers.discord-rag-api.entrypoints=websecure"
      - "traefik.http.routers.discord-rag-api.tls.certresolver=letsencrypt"
      - "traefik.http.services.discord-rag-api.loadbalancer.server.port=8000"
      - "com.centurylinklabs.watchtower.enable=true"

networks:
  traefik-public:
    external: true

```

**⚠️ IMPORTANTE:** Substitua `bot.seudominio.com` pelo seu domínio real!

### 2.2 Criar `.env`

```bash
nano .env
```

Cole e configure suas credenciais:

```env
# Discord Bot Token
DISCORD_TOKEN=seu_token_discord_aqui

# OpenAI API Key (para embeddings)
OPENAI_API_KEY=sua_chave_openai_aqui

# OpenRouter API Key (para LLM)
OPENROUTER_API_KEY=sua_chave_openrouter_aqui
OPENROUTER_MODEL=minimax/minimax-m2:free

# Supabase Configuration
SUPABASE_URL=https://seu-projeto.supabase.co
SUPABASE_API_KEY=sua_chave_supabase_aqui

# Optional Configuration
LOG_LEVEL=INFO
CACHE_ENABLED=true
```

**🔒 SEGURANÇA:** Proteja este arquivo!

```bash
chmod 600 .env
```

---

## 📂 Passo 3: Copiar Código do Bot

### Opção A: Via Git (Recomendado)

```bash
cd /opt/discord-rag-bot
git clone https://github.com/prof-ramos/DiscordRAGBot.git temp
cp -r temp/src .
cp temp/bot.py .
cp temp/api_server.py .
cp temp/requirements.txt .
cp -r temp/web .
rm -rf temp
```

### Opção B: Via SCP (do seu computador local)

```bash
# No seu computador local
scp -r src/ usuario@seu-servidor:/opt/discord-rag-bot/
scp bot.py api_server.py requirements.txt usuario@seu-servidor:/opt/discord-rag-bot/
scp -r web/ usuario@seu-servidor:/opt/discord-rag-bot/
```

---

## 🗄️ Passo 4: Configurar Supabase

### 4.1 Criar Extensão pgvector

Acesse o SQL Editor no Supabase e execute:

```sql
CREATE EXTENSION IF NOT EXISTS vector;
```

### 4.2 Criar Tabela de Documentos

```sql
CREATE TABLE IF NOT EXISTS documents (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    content TEXT NOT NULL,
    metadata JSONB,
    embedding VECTOR(1536),
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Criar índice para busca vetorial
CREATE INDEX ON documents USING ivfflat (embedding vector_cosine_ops)
WITH (lists = 100);
```

### 4.3 Criar Função de Busca

```sql
CREATE OR REPLACE FUNCTION match_documents(
    query_embedding VECTOR(1536),
    match_threshold FLOAT,
    match_count INT
)
RETURNS TABLE (
    id UUID,
    content TEXT,
    metadata JSONB,
    similarity FLOAT
)
LANGUAGE SQL STABLE
AS $$
    SELECT
        id,
        content,
        metadata,
        1 - (documents.embedding <=> query_embedding) AS similarity
    FROM documents
    WHERE 1 - (documents.embedding <=> query_embedding) > match_threshold
    ORDER BY similarity DESC
    LIMIT match_count;
$$;
```

---

## 📚 Passo 5: Indexar Documentos

### 5.1 Adicionar Documentos

```bash
cd /opt/discord-rag-bot
# Copie seus PDFs para a pasta data/
cp ~/meus-documentos/*.pdf data/
```

### 5.2 Executar Indexação

```bash
# Criar container temporário para indexação
docker run --rm -it \
    -v $(pwd)/src:/app/src \
    -v $(pwd)/load.py:/app/load.py \
    -v $(pwd)/data:/app/data \
    -v $(pwd)/requirements.txt:/app/requirements.txt \
    --env-file .env \
    python:3.11-slim \
    sh -c "
        pip install --no-cache-dir -q -r /app/requirements.txt &&
        cd /app &&
        python load.py
    "
```

Aguarde a mensagem:
```
✅ INDEXAÇÃO COMPLETA!
📊 Total de vetores: XXX
```

---

## 🚀 Passo 6: Deploy via Portainer

### 6.1 Acessar Portainer

```
https://portainer.seudominio.com
```

### 6.2 Criar Stack

1. **Menu lateral:** Stacks → Add stack
2. **Nome:** `discord-rag-bot`
3. **Build method:** Git Repository
4. **Repository URL:** `https://github.com/prof-ramos/DiscordRAGBot`
5. **Repository reference:** `main`
6. **Compose path:** `docker-compose.yml`

**OU** Cole o conteúdo do `docker-compose.yml` manualmente.

### 6.3 Configurar Environment Variables

Na seção **Environment variables**, adicione:

```
DISCORD_TOKEN=seu_token
OPENAI_API_KEY=sua_chave
OPENROUTER_API_KEY=sua_chave
SUPABASE_URL=sua_url
SUPABASE_API_KEY=sua_chave
```

### 6.4 Deploy

Clique em **Deploy the stack**

---

## 🌐 Passo 7: Configurar Domínio (Traefik)

### 7.1 Criar Registro DNS

No seu provedor de DNS (Cloudflare, etc.):

```
Tipo: A
Nome: bot
Valor: IP_DA_SUA_VPS
TTL: Auto
```

### 7.2 Verificar Roteamento

Traefik automaticamente:
- ✅ Detecta o container `api-server`
- ✅ Cria rota para `bot.seudominio.com`
- ✅ Gera certificado SSL via Let's Encrypt

### 7.3 Testar Acesso

```bash
curl https://bot.seudominio.com/api/health
```

Deve retornar:
```json
{
  "status": "healthy",
  "timestamp": "2025-11-09T..."
}
```

---

## ✅ Passo 8: Verificação

### 8.1 Verificar Containers

```bash
docker ps
```

Deve mostrar:
```
CONTAINER ID   IMAGE              STATUS         PORTS      NAMES
xxxxx          python:3.11-slim   Up 2 minutes              discord-rag-bot
xxxxx          python:3.11-slim   Up 2 minutes              discord-rag-api
```

### 8.2 Verificar Logs do Bot

```bash
docker logs -f discord-rag-bot
```

Deve mostrar:
```
✅ RAG carregado | Modelo: minimax/minimax-m2:free
🤖 Bot iniciado | Nome: SeuBot#1234
⚙️ Comandos sincronizados | Total: 3
```

### 8.3 Verificar Logs da API

```bash
docker logs -f discord-rag-api
```

Deve mostrar:
```
INFO:     Started server process
INFO:     Uvicorn running on http://0.0.0.0:8000
INFO:     Application startup complete
```

### 8.4 Acessar Interface Web

Abra no navegador:
```
https://bot.seudominio.com
```

Você deve ver a interface terminal do bot! 🎉

---

## 🔄 Atualizações e Manutenção

### Atualizar o Bot

```bash
cd /opt/discord-rag-bot
git pull origin main
docker-compose down
docker-compose up -d
```

### Ver Logs em Tempo Real

```bash
# Bot Discord
docker logs -f discord-rag-bot

# API Web
docker logs -f discord-rag-api

# Ambos
docker-compose logs -f
```

### Reiniciar Serviços

```bash
# Reiniciar tudo
docker-compose restart

# Reiniciar apenas o bot
docker-compose restart discord-bot

# Reiniciar apenas a API
docker-compose restart api-server
```

### Atualizar Documentos

```bash
# 1. Adicionar novos documentos
cp ~/novos-docs/*.pdf /opt/discord-rag-bot/data/

# 2. Re-indexar
docker-compose run --rm discord-bot python load.py
```

---

## 🛡️ Segurança

### Firewall

```bash
# Permitir apenas SSH, HTTP e HTTPS
sudo ufw allow 22/tcp
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp
sudo ufw enable
```

### Backup do .env

```bash
# Fazer backup seguro
cp .env .env.backup
gpg -c .env.backup  # Criptografar
rm .env.backup      # Remover não criptografado
```

### Monitoramento de Logs

```bash
# Criar alerta para erros
cat << 'EOF' > /opt/discord-rag-bot/check_errors.sh
#!/bin/bash
ERRORS=$(docker logs discord-rag-bot --since 1h 2>&1 | grep -c ERROR)
if [ $ERRORS -gt 10 ]; then
    echo "ALERTA: $ERRORS erros no bot nas últimas horas!" | mail -s "Discord Bot Error" seu@email.com
fi
EOF

chmod +x /opt/discord-rag-bot/check_errors.sh

# Adicionar ao cron (executar a cada hora)
(crontab -l 2>/dev/null; echo "0 * * * * /opt/discord-rag-bot/check_errors.sh") | crontab -
```

---

## 📊 Monitoramento via Portainer

### 1. Verificar Status

Portainer → Containers → `discord-rag-bot`

Você verá:
- ✅ Status: Running
- 📊 CPU: ~5-10%
- 💾 Memory: ~200-300 MB

### 2. Ver Logs

Portainer → Containers → `discord-rag-bot` → Logs

### 3. Estatísticas

Portainer → Containers → `discord-rag-bot` → Stats

---

## 🚨 Troubleshooting

### Bot não inicia

```bash
# Ver erros detalhados
docker logs discord-rag-bot

# Verificar variáveis de ambiente
docker exec discord-rag-bot env | grep DISCORD_TOKEN

# Testar manualmente
docker exec -it discord-rag-bot bash
python bot.py
```

### API não responde

```bash
# Verificar se está ouvindo
docker exec discord-rag-api netstat -tlnp

# Verificar logs do Traefik
docker logs traefik

# Testar internamente
docker exec discord-rag-api curl http://localhost:8000/api/health
```

### Certificado SSL não gerado

```bash
# Verificar logs do Traefik
docker logs traefik | grep -i certificate

# Forçar renovação
docker exec traefik traefik healthcheck
```

### Documentos não indexados

```bash
# Verificar se há documentos
ls -lh /opt/discord-rag-bot/data/

# Re-executar indexação com debug
docker-compose run --rm discord-bot python -u load.py
```

---

## 🎯 Comandos Úteis

### Gerenciamento Rápido

```bash
# Iniciar
docker-compose up -d

# Parar
docker-compose down

# Restart
docker-compose restart

# Ver status
docker-compose ps

# Ver logs
docker-compose logs -f

# Atualizar imagens
docker-compose pull
docker-compose up -d
```

### Limpeza

```bash
# Remover containers parados
docker container prune -f

# Remover imagens não utilizadas
docker image prune -f

# Remover volumes não utilizados
docker volume prune -f

# Limpeza completa
docker system prune -af
```

---

## 📈 Escalabilidade

### Auto-scaling com Docker Swarm

```bash
# Inicializar Swarm
docker swarm init

# Deploy como stack
docker stack deploy -c docker-compose.yml discord-rag

# Escalar API
docker service scale discord-rag_api-server=3
```

### Load Balancing com Traefik

Traefik automaticamente distribui carga entre réplicas.

---

## 🎉 Conclusão

Seu Discord RAG Bot está agora:

✅ **Rodando 24/7** na VPS
✅ **Com HTTPS** via Traefik + Let's Encrypt
✅ **Interface Web** acessível publicamente
✅ **Monitorado** via Portainer
✅ **Auto-restart** em caso de falhas
✅ **Logs centralizados**

**Acesse:** `https://bot.seudominio.com`

---

## 📞 Suporte

- **Documentação:** https://github.com/prof-ramos/DiscordRAGBot
- **Issues:** https://github.com/prof-ramos/DiscordRAGBot/issues
- **Discord:** [Link do servidor de suporte]

---

## 📄 Licença

MIT License - Uso livre!
