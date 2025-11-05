#!/bin/bash
# ============================================================================
# Docker Build Script
# ============================================================================
# Builds optimized Docker image with proper tagging and caching
# ============================================================================

set -e

# Colors
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Variables
IMAGE_NAME="discord-rag-bot"
VERSION="${VERSION:-2.0.0}"
BUILD_DATE=$(date -u +"%Y-%m-%dT%H:%M:%SZ")
VCS_REF=$(git rev-parse --short HEAD 2>/dev/null || echo "unknown")

# Registry (optional)
REGISTRY="${REGISTRY:-}"
if [ -n "$REGISTRY" ]; then
    FULL_IMAGE_NAME="${REGISTRY}/${IMAGE_NAME}"
else
    FULL_IMAGE_NAME="${IMAGE_NAME}"
fi

echo -e "${BLUE}============================================${NC}"
echo -e "${BLUE}Docker Build Script${NC}"
echo -e "${BLUE}============================================${NC}"
echo -e "${GREEN}Image:${NC} ${FULL_IMAGE_NAME}:${VERSION}"
echo -e "${GREEN}Build Date:${NC} ${BUILD_DATE}"
echo -e "${GREEN}VCS Ref:${NC} ${VCS_REF}"
echo ""

# Build the image
echo -e "${YELLOW}Building Docker image...${NC}"
docker build \
    --build-arg BUILD_DATE="${BUILD_DATE}" \
    --build-arg VCS_REF="${VCS_REF}" \
    --build-arg VERSION="${VERSION}" \
    --tag "${FULL_IMAGE_NAME}:${VERSION}" \
    --tag "${FULL_IMAGE_NAME}:latest" \
    --file Dockerfile \
    .

if [ $? -eq 0 ]; then
    echo -e "${GREEN}✓ Build successful!${NC}"
else
    echo -e "${RED}✗ Build failed!${NC}"
    exit 1
fi

# Display image info
echo ""
echo -e "${BLUE}Image Information:${NC}"
docker images "${FULL_IMAGE_NAME}" --format "table {{.Repository}}\t{{.Tag}}\t{{.Size}}\t{{.CreatedAt}}"

# Security scan (if trivy is installed)
if command -v trivy &> /dev/null; then
    echo ""
    echo -e "${YELLOW}Running security scan...${NC}"
    trivy image --severity HIGH,CRITICAL "${FULL_IMAGE_NAME}:${VERSION}"
else
    echo -e "${YELLOW}⚠ Trivy not installed. Skipping security scan.${NC}"
    echo -e "${YELLOW}Install with: brew install trivy (or apt-get install trivy)${NC}"
fi

echo ""
echo -e "${GREEN}============================================${NC}"
echo -e "${GREEN}Build Complete!${NC}"
echo -e "${GREEN}============================================${NC}"
echo -e "Tagged as:"
echo -e "  • ${FULL_IMAGE_NAME}:${VERSION}"
echo -e "  • ${FULL_IMAGE_NAME}:latest"
echo ""
echo -e "Next steps:"
echo -e "  • Test: ${BLUE}docker run --rm --env-file .env ${FULL_IMAGE_NAME}:${VERSION}${NC}"
echo -e "  • Push: ${BLUE}docker push ${FULL_IMAGE_NAME}:${VERSION}${NC}"
echo -e "  • Deploy: ${BLUE}docker-compose up -d${NC}"
echo ""
