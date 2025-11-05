# ============================================================================
# Discord RAG Bot - Production Dockerfile
# ============================================================================
# Multi-stage build for optimized, secure, production-ready container
# ============================================================================

# ============================================================================
# Stage 1: Builder - Install dependencies and build application
# ============================================================================
FROM python:3.11-slim as builder

# Metadata
LABEL maintainer="prof.ramos@example.com"
LABEL description="Discord RAG Bot - Production Build Stage"

# Set environment variables for build
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    PIP_DEFAULT_TIMEOUT=100

# Install system dependencies required for building Python packages
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Create virtual environment
RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# Copy only requirements first for better caching
COPY requirements-prod.txt /tmp/

# Install Python dependencies in virtual environment
RUN pip install --upgrade pip setuptools wheel && \
    pip install -r /tmp/requirements-prod.txt && \
    pip install gunicorn  # For potential future web interface

# ============================================================================
# Stage 2: Runtime - Minimal production image
# ============================================================================
FROM python:3.11-slim

# Metadata
LABEL maintainer="prof.ramos@example.com"
LABEL description="Discord RAG Bot - Production Runtime"
LABEL version="2.0.0"
LABEL org.opencontainers.image.source="https://github.com/prof-ramos/DiscordRAGBot"

# Set environment variables
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PATH="/opt/venv/bin:$PATH" \
    # Application settings
    APP_HOME=/app \
    # User settings
    APP_USER=botuser \
    APP_UID=10001

# Install runtime dependencies only
RUN apt-get update && apt-get install -y --no-install-recommends \
    # Required for psycopg2 (PostgreSQL client)
    libpq5 \
    # Useful for debugging
    curl \
    # Timezone data
    tzdata \
    && rm -rf /var/lib/apt/lists/* \
    && apt-get clean

# Copy virtual environment from builder
COPY --from=builder /opt/venv /opt/venv

# Create non-root user for security
RUN groupadd -g ${APP_UID} ${APP_USER} && \
    useradd -u ${APP_UID} -g ${APP_USER} -s /bin/bash -m ${APP_USER}

# Create app directory and set permissions
RUN mkdir -p ${APP_HOME}/data ${APP_HOME}/logs && \
    chown -R ${APP_USER}:${APP_USER} ${APP_HOME}

# Set working directory
WORKDIR ${APP_HOME}

# Copy application code
COPY --chown=${APP_USER}:${APP_USER} . ${APP_HOME}/

# Create entrypoint script
COPY --chown=${APP_USER}:${APP_USER} docker/entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh

# Create health check script
COPY --chown=${APP_USER}:${APP_USER} docker/healthcheck.sh /healthcheck.sh
RUN chmod +x /healthcheck.sh

# Switch to non-root user
USER ${APP_USER}

# Expose port (if needed for future web interface)
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD /healthcheck.sh || exit 1

# Set entrypoint
ENTRYPOINT ["/entrypoint.sh"]

# Default command
CMD ["python", "bot.py"]

# ============================================================================
# Build Arguments (for CI/CD)
# ============================================================================
ARG BUILD_DATE
ARG VCS_REF
ARG VERSION=2.0.0

LABEL org.opencontainers.image.created="${BUILD_DATE}"
LABEL org.opencontainers.image.revision="${VCS_REF}"
LABEL org.opencontainers.image.version="${VERSION}"
