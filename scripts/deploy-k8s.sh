#!/bin/bash
# ============================================================================
# Kubernetes Deployment Script
# ============================================================================
# Deploys Discord RAG Bot to Kubernetes cluster
# ============================================================================

set -e

# Colors
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

# Variables
NAMESPACE="discord-rag-bot"
KUBECTL="kubectl"

echo -e "${BLUE}============================================${NC}"
echo -e "${BLUE}Kubernetes Deployment Script${NC}"
echo -e "${BLUE}============================================${NC}"

# Check if kubectl is available
if ! command -v ${KUBECTL} &> /dev/null; then
    echo -e "${RED}✗ kubectl not found!${NC}"
    echo -e "Please install kubectl: https://kubernetes.io/docs/tasks/tools/"
    exit 1
fi

# Check if connected to cluster
echo -e "${YELLOW}Checking cluster connection...${NC}"
if ! ${KUBECTL} cluster-info &> /dev/null; then
    echo -e "${RED}✗ Not connected to Kubernetes cluster!${NC}"
    exit 1
fi

CURRENT_CONTEXT=$(${KUBECTL} config current-context)
echo -e "${GREEN}✓ Connected to:${NC} ${CURRENT_CONTEXT}"

# Confirm deployment
echo ""
echo -e "${YELLOW}⚠ You are about to deploy to: ${CURRENT_CONTEXT}${NC}"
read -p "Continue? (y/N) " -n 1 -r
echo
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo "Deployment cancelled."
    exit 0
fi

# Create secrets (if not exists)
echo ""
echo -e "${YELLOW}Checking secrets...${NC}"
if ! ${KUBECTL} get secret discord-rag-bot-secrets -n ${NAMESPACE} &> /dev/null; then
    echo -e "${RED}✗ Secret 'discord-rag-bot-secrets' not found!${NC}"
    echo ""
    echo "Create the secret with:"
    echo ""
    echo "${KUBECTL} create secret generic discord-rag-bot-secrets \\"
    echo "  --from-literal=DISCORD_TOKEN=your_token \\"
    echo "  --from-literal=OPENAI_API_KEY=your_key \\"
    echo "  --from-literal=OPENROUTER_API_KEY=your_key \\"
    echo "  --from-literal=SUPABASE_URL=your_url \\"
    echo "  --from-literal=SUPABASE_API_KEY=your_key \\"
    echo "  -n ${NAMESPACE}"
    echo ""
    exit 1
else
    echo -e "${GREEN}✓ Secret found${NC}"
fi

# Apply manifests
echo ""
echo -e "${YELLOW}Applying Kubernetes manifests...${NC}"

# Apply in order
${KUBECTL} apply -f k8s/deployment.yaml
${KUBECTL} apply -f k8s/hpa.yaml

# Wait for rollout
echo ""
echo -e "${YELLOW}Waiting for deployment to complete...${NC}"
${KUBECTL} rollout status deployment/discord-rag-bot -n ${NAMESPACE} --timeout=5m

# Check status
echo ""
echo -e "${GREEN}✓ Deployment complete!${NC}"
echo ""
echo -e "${BLUE}Pod Status:${NC}"
${KUBECTL} get pods -n ${NAMESPACE} -l app=discord-rag-bot

echo ""
echo -e "${BLUE}Deployment Info:${NC}"
${KUBECTL} describe deployment discord-rag-bot -n ${NAMESPACE} | grep -A 5 "Replicas:"

# Show logs
echo ""
echo -e "${YELLOW}Recent logs:${NC}"
${KUBECTL} logs -n ${NAMESPACE} -l app=discord-rag-bot --tail=20

echo ""
echo -e "${GREEN}============================================${NC}"
echo -e "${GREEN}Deployment Complete!${NC}"
echo -e "${GREEN}============================================${NC}"
echo -e "Useful commands:"
echo -e "  • Logs: ${BLUE}${KUBECTL} logs -n ${NAMESPACE} -l app=discord-rag-bot -f${NC}"
echo -e "  • Shell: ${BLUE}${KUBECTL} exec -it -n ${NAMESPACE} <pod-name> -- /bin/bash${NC}"
echo -e "  • Status: ${BLUE}${KUBECTL} get all -n ${NAMESPACE}${NC}"
echo ""
