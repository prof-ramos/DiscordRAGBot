# 🐳 Docker Deployment Guide

Complete guide for deploying Discord RAG Bot using Docker and Kubernetes.

## 📋 Table of Contents

- [Quick Start](#quick-start)
- [Docker](#docker)
- [Docker Compose](#docker-compose)
- [Kubernetes](#kubernetes)
- [Production Deployment](#production-deployment)
- [Monitoring & Logging](#monitoring--logging)
- [Troubleshooting](#troubleshooting)

---

## 🚀 Quick Start

### Prerequisites

- Docker 20.10+ and Docker Compose 2.0+
- Git
- API keys (Discord, OpenAI, OpenRouter, Supabase)

### 1. Clone and Configure

```bash
git clone https://github.com/prof-ramos/DiscordRAGBot.git
cd DiscordRAGBot

# Create environment file
cp .env.example .env
# Edit .env with your API keys
nano .env
```

### 2. Build and Run

```bash
# Build image
./scripts/build.sh

# Run with Docker Compose
docker-compose up -d

# View logs
docker-compose logs -f
```

---

## 🐳 Docker

### Building the Image

```bash
# Simple build
docker build -t discord-rag-bot:latest .

# Build with custom version
docker build \
  --build-arg VERSION=2.1.0 \
  --tag discord-rag-bot:2.1.0 \
  .

# Use build script (recommended)
./scripts/build.sh
```

### Running the Container

```bash
# Run with environment file
docker run -d \
  --name discord-rag-bot \
  --env-file .env \
  --restart unless-stopped \
  -v $(pwd)/data:/app/data \
  -v $(pwd)/logs:/app/logs \
  discord-rag-bot:latest

# Run interactively (for debugging)
docker run -it --rm \
  --env-file .env \
  discord-rag-bot:latest \
  /bin/bash
```

### Image Details

**Base Image:** `python:3.11-slim`

**Size:** ~500MB (optimized with multi-stage build)

**Layers:**
1. Builder stage: Install dependencies
2. Runtime stage: Copy app and virtual environment
3. Security: Non-root user (UID 10001)
4. Health checks: Built-in monitoring

**Security Features:**
- ✅ Multi-stage build (minimal attack surface)
- ✅ Non-root user
- ✅ Read-only root filesystem
- ✅ Dropped capabilities
- ✅ Security scanning ready

---

## 🎼 Docker Compose

### Development Environment

```bash
# Start
docker-compose up -d

# View logs
docker-compose logs -f bot

# Stop
docker-compose down

# Rebuild
docker-compose up -d --build
```

**Features:**
- Hot-reload (source code mounted as volume)
- Debug logging
- Local data persistence
- Resource limits

### Production Environment

```bash
# Use production compose file
docker-compose -f docker-compose.prod.yml up -d

# View logs
docker-compose -f docker-compose.prod.yml logs -f

# Scale (not recommended for Discord bot)
docker-compose -f docker-compose.prod.yml up -d --scale bot=1
```

**Features:**
- Optimized for production
- Read-only volumes where possible
- Stricter resource limits
- Security hardening
- Structured logging

### Useful Commands

```bash
# View resource usage
docker-compose ps
docker stats

# Execute command in container
docker-compose exec bot python -m src.cli stats

# Restart bot
docker-compose restart bot

# View health status
docker inspect discord-rag-bot-dev | grep -A 10 Health
```

---

## ☸️ Kubernetes

### Prerequisites

```bash
# Install kubectl
# macOS
brew install kubectl

# Linux
curl -LO "https://dl.k8s.io/release/$(curl -L -s https://dl.k8s.io/release/stable.txt)/bin/linux/amd64/kubectl"

# Verify
kubectl version --client
```

### 1. Create Secrets

```bash
# Create namespace
kubectl create namespace discord-rag-bot

# Create secrets
kubectl create secret generic discord-rag-bot-secrets \
  --from-literal=DISCORD_TOKEN=your_discord_token \
  --from-literal=OPENAI_API_KEY=your_openai_key \
  --from-literal=OPENROUTER_API_KEY=your_openrouter_key \
  --from-literal=SUPABASE_URL=your_supabase_url \
  --from-literal=SUPABASE_API_KEY=your_supabase_key \
  -n discord-rag-bot
```

### 2. Deploy

```bash
# Apply manifests
kubectl apply -f k8s/deployment.yaml
kubectl apply -f k8s/hpa.yaml

# Or use script
./scripts/deploy-k8s.sh

# Check status
kubectl get all -n discord-rag-bot
```

### 3. Manage Deployment

```bash
# View logs
kubectl logs -n discord-rag-bot -l app=discord-rag-bot -f

# Get pod shell
kubectl exec -it -n discord-rag-bot <pod-name> -- /bin/bash

# Restart deployment
kubectl rollout restart deployment/discord-rag-bot -n discord-rag-bot

# View events
kubectl get events -n discord-rag-bot --sort-by='.lastTimestamp'

# Check resource usage
kubectl top pods -n discord-rag-bot
```

### Storage Configuration

**Persistent Volumes:**
- `/app/logs` - 5Gi (Logs storage)
- `/app/data` - 10Gi (Document storage)
- `/home/botuser/.cache` - 500Mi emptyDir (Cache)

**Storage Class:**
```yaml
# Update in k8s/deployment.yaml
storageClassName: your-storage-class
```

### Resource Limits

```yaml
resources:
  requests:
    cpu: "500m"
    memory: "1Gi"
  limits:
    cpu: "2000m"
    memory: "4Gi"
```

**Adjust based on your workload!**

---

## 🏭 Production Deployment

### Pre-deployment Checklist

- [ ] Environment variables configured
- [ ] Secrets created securely
- [ ] Persistent storage configured
- [ ] Resource limits set appropriately
- [ ] Monitoring and logging enabled
- [ ] Backup strategy in place
- [ ] Rollback plan ready

### CI/CD Integration

**GitHub Actions Example:**

```yaml
# .github/workflows/docker.yml
name: Docker Build and Push

on:
  push:
    tags:
      - 'v*'

jobs:
  build:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - name: Build and push
        uses: docker/build-push-action@v5
        with:
          push: true
          tags: |
            ghcr.io/${{ github.repository }}:${{ github.ref_name }}
            ghcr.io/${{ github.repository }}:latest
```

### Security Scanning

```bash
# Scan with Trivy
trivy image discord-rag-bot:latest

# Scan with Snyk
snyk container test discord-rag-bot:latest

# Scan with Docker Scout
docker scout cves discord-rag-bot:latest
```

### Health Checks

**Container Level:**
```bash
# Check health status
docker inspect discord-rag-bot | jq '.[0].State.Health'

# View health check logs
docker inspect discord-rag-bot | jq '.[0].State.Health.Log'
```

**Kubernetes Level:**
```bash
# Check probes
kubectl describe pod -n discord-rag-bot <pod-name> | grep -A 5 Liveness
```

---

## 📊 Monitoring & Logging

### Logs

**Docker:**
```bash
# View logs
docker logs -f discord-rag-bot

# Last 100 lines
docker logs --tail 100 discord-rag-bot

# Since timestamp
docker logs --since 2h discord-rag-bot
```

**Docker Compose:**
```bash
# All services
docker-compose logs -f

# Specific service
docker-compose logs -f bot

# Last N lines
docker-compose logs --tail=50 bot
```

**Kubernetes:**
```bash
# Current logs
kubectl logs -n discord-rag-bot -l app=discord-rag-bot

# Follow logs
kubectl logs -n discord-rag-bot -l app=discord-rag-bot -f

# Previous container
kubectl logs -n discord-rag-bot <pod-name> --previous
```

### Metrics

**Resource Usage:**
```bash
# Docker
docker stats discord-rag-bot

# Docker Compose
docker-compose ps
docker stats $(docker-compose ps -q)

# Kubernetes
kubectl top pods -n discord-rag-bot
kubectl top nodes
```

### Log Aggregation

**Example: ELK Stack**

```yaml
# Add to docker-compose.prod.yml
logging:
  driver: "fluentd"
  options:
    fluentd-address: localhost:24224
    tag: discord-rag-bot
```

**Example: Loki**

```yaml
logging:
  driver: "loki"
  options:
    loki-url: "http://localhost:3100/loki/api/v1/push"
```

---

## 🔧 Troubleshooting

### Common Issues

#### 1. Container Fails to Start

**Check logs:**
```bash
docker logs discord-rag-bot
```

**Common causes:**
- Missing environment variables
- Invalid API keys
- Network connectivity issues
- Permission problems

#### 2. Health Check Failing

**Debug:**
```bash
# Run health check manually
docker exec discord-rag-bot /healthcheck.sh

# Check PID file
docker exec discord-rag-bot cat /tmp/bot.pid

# Check if process is running
docker exec discord-rag-bot ps aux
```

#### 3. Out of Memory

**Symptoms:**
```
docker logs discord-rag-bot
# Shows: Killed
```

**Solutions:**
```bash
# Increase memory limit
docker run -m 4g discord-rag-bot:latest

# Or in docker-compose.yml
deploy:
  resources:
    limits:
      memory: 4G
```

#### 4. Cannot Connect to Supabase

**Debug:**
```bash
# Test connectivity
docker exec discord-rag-bot curl -v https://your-project.supabase.co

# Check DNS resolution
docker exec discord-rag-bot nslookup your-project.supabase.co

# Verify environment variable
docker exec discord-rag-bot env | grep SUPABASE
```

#### 5. Permission Denied

**If mounting volumes:**
```bash
# Fix ownership
sudo chown -R 10001:10001 ./data ./logs

# Or run with user mapping
docker run -u $(id -u):$(id -g) ...
```

### Debug Mode

**Run with shell:**
```bash
docker run -it --rm \
  --env-file .env \
  discord-rag-bot:latest \
  /bin/bash
```

**Override entrypoint:**
```bash
docker run -it --rm \
  --env-file .env \
  --entrypoint /bin/bash \
  discord-rag-bot:latest
```

### Performance Optimization

**Build optimizations:**
```bash
# Use BuildKit
DOCKER_BUILDKIT=1 docker build -t discord-rag-bot:latest .

# Cache mount
docker build \
  --build-arg BUILDKIT_INLINE_CACHE=1 \
  -t discord-rag-bot:latest .
```

**Runtime optimizations:**
```bash
# Limit CPU
docker run --cpus="1.5" discord-rag-bot:latest

# Set memory reservation
docker run -m 2g --memory-reservation 1g discord-rag-bot:latest
```

---

## 📚 Additional Resources

### Documentation

- [Docker Best Practices](https://docs.docker.com/develop/dev-best-practices/)
- [Kubernetes Documentation](https://kubernetes.io/docs/)
- [Docker Security](https://docs.docker.com/engine/security/)

### Tools

- **Trivy**: Container scanning
- **Docker Scout**: Security analysis
- **Dive**: Image layer analysis
- **Hadolint**: Dockerfile linting

### Commands Reference

```bash
# Build
./scripts/build.sh

# Run (Docker)
docker run --env-file .env discord-rag-bot:latest

# Run (Compose - Dev)
docker-compose up -d

# Run (Compose - Prod)
docker-compose -f docker-compose.prod.yml up -d

# Deploy (Kubernetes)
./scripts/deploy-k8s.sh

# Logs
docker logs -f discord-rag-bot                    # Docker
docker-compose logs -f bot                         # Compose
kubectl logs -n discord-rag-bot -l app=discord-rag-bot -f  # K8s

# Shell
docker exec -it discord-rag-bot /bin/bash         # Docker
docker-compose exec bot /bin/bash                  # Compose
kubectl exec -it -n discord-rag-bot <pod> -- /bin/bash  # K8s
```

---

**Version:** 2.0.0
**Last Updated:** 2025-11-05
**Maintainer:** Prof. Ramos
**Status:** ✅ Production Ready
