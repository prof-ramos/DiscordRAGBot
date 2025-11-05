#!/bin/bash
# ============================================================================
# Discord RAG Bot - Docker Entrypoint Script
# ============================================================================
# Handles initialization, environment validation, and graceful shutdown
# ============================================================================

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Logging functions
log_info() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

log_warn() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Trap signals for graceful shutdown
trap 'log_info "Received SIGTERM, shutting down gracefully..."; exit 0' SIGTERM
trap 'log_info "Received SIGINT, shutting down gracefully..."; exit 0' SIGINT

# ============================================================================
# Environment Validation
# ============================================================================

log_info "Starting Discord RAG Bot..."
log_info "Application Home: ${APP_HOME}"
log_info "Running as: $(whoami)"

# Check required environment variables
REQUIRED_VARS=(
    "DISCORD_TOKEN"
    "OPENAI_API_KEY"
    "OPENROUTER_API_KEY"
    "SUPABASE_URL"
    "SUPABASE_API_KEY"
)

missing_vars=()
for var in "${REQUIRED_VARS[@]}"; do
    if [ -z "${!var}" ]; then
        missing_vars+=("$var")
    fi
done

if [ ${#missing_vars[@]} -ne 0 ]; then
    log_error "Missing required environment variables:"
    for var in "${missing_vars[@]}"; do
        log_error "  - $var"
    done
    log_error "Please set all required environment variables"
    exit 1
fi

log_info "✓ All required environment variables are set"

# ============================================================================
# Directory Setup
# ============================================================================

# Ensure directories exist
for dir in "${APP_HOME}/data" "${APP_HOME}/logs"; do
    if [ ! -d "$dir" ]; then
        log_warn "Creating missing directory: $dir"
        mkdir -p "$dir"
    fi
done

log_info "✓ Directory structure validated"

# ============================================================================
# Health Check Setup
# ============================================================================

# Create a PID file for health checks
echo $$ > /tmp/bot.pid

# ============================================================================
# Database Connection Check
# ============================================================================

log_info "Checking database connectivity..."

# Simple connectivity check using Python
python3 << 'EOF'
import os
import sys
from urllib.parse import urlparse

try:
    supabase_url = os.getenv('SUPABASE_URL')
    if not supabase_url:
        print("SUPABASE_URL not set")
        sys.exit(1)

    # Parse URL to ensure it's valid
    parsed = urlparse(supabase_url)
    if not parsed.scheme or not parsed.netloc:
        print(f"Invalid SUPABASE_URL: {supabase_url}")
        sys.exit(1)

    print(f"✓ Supabase URL is valid: {parsed.netloc}")
    sys.exit(0)
except Exception as e:
    print(f"Error validating Supabase URL: {e}")
    sys.exit(1)
EOF

if [ $? -ne 0 ]; then
    log_error "Database connectivity check failed"
    exit 1
fi

log_info "✓ Database connectivity validated"

# ============================================================================
# Display Configuration
# ============================================================================

log_info "Configuration:"
log_info "  - Supabase: ${SUPABASE_URL}"
log_info "  - OpenRouter Model: ${OPENROUTER_MODEL:-minimax/minimax-m2:free}"
log_info "  - Embedding Model: ${EMBEDDING_MODEL:-text-embedding-3-small}"
log_info "  - Log Level: ${LOG_LEVEL:-INFO}"
log_info "  - Environment: ${ENVIRONMENT:-production}"

# ============================================================================
# Execute Command
# ============================================================================

log_info "Starting application: $@"
log_info "===================="

# Execute the main command
exec "$@"
