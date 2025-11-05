# ============================================================================
# Discord RAG Bot - Makefile
# ============================================================================
# Common development commands for the Discord RAG Bot project.
#
# Usage:
#   make help          - Show this help message
#   make install       - Install production dependencies
#   make install-dev   - Install development dependencies
#   make test          - Run tests
#   make format        - Format code
#   make lint          - Run linters
#   make run           - Run the bot
# ============================================================================

.PHONY: help
help:  ## Show this help message
	@echo "Discord RAG Bot - Available Commands:"
	@echo ""
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | \
		awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-20s\033[0m %s\n", $$1, $$2}'
	@echo ""

# ============================================================================
# Installation & Setup
# ============================================================================

.PHONY: install
install:  ## Install production dependencies
	pip install -r requirements-prod.txt

.PHONY: install-dev
install-dev:  ## Install development dependencies
	pip install -r requirements-dev.txt
	pre-commit install
	pre-commit install --hook-type commit-msg

.PHONY: install-editable
install-editable:  ## Install package in editable mode
	pip install -e .

.PHONY: install-all
install-all: install-dev install-editable  ## Install everything (dev + editable)
	@echo "✅ All dependencies installed!"

.PHONY: update
update:  ## Update all dependencies
	pip install --upgrade -r requirements-dev.txt
	pre-commit autoupdate

# ============================================================================
# Code Quality
# ============================================================================

.PHONY: format
format:  ## Format code with black and isort
	@echo "🎨 Formatting code..."
	black src tests bot.py load.py
	isort src tests bot.py load.py
	@echo "✅ Code formatted!"

.PHONY: lint
lint:  ## Run all linters
	@echo "🔍 Running linters..."
	ruff check src tests
	mypy src
	bandit -r src -c pyproject.toml
	@echo "✅ Linting complete!"

.PHONY: lint-fix
lint-fix:  ## Run linters and auto-fix issues
	@echo "🔧 Running linters with auto-fix..."
	ruff check --fix src tests
	@echo "✅ Auto-fixes applied!"

.PHONY: typecheck
typecheck:  ## Run type checking with mypy
	@echo "🔍 Type checking..."
	mypy src
	@echo "✅ Type check complete!"

.PHONY: security
security:  ## Run security checks
	@echo "🔒 Running security checks..."
	bandit -r src -c pyproject.toml
	safety check --short-report
	@echo "✅ Security check complete!"

.PHONY: check
check: format lint typecheck  ## Run all code quality checks
	@echo "✅ All checks passed!"

# ============================================================================
# Testing
# ============================================================================

.PHONY: test
test:  ## Run tests with coverage
	@echo "🧪 Running tests..."
	pytest

.PHONY: test-fast
test-fast:  ## Run tests without coverage (faster)
	@echo "⚡ Running fast tests..."
	pytest --no-cov -x

.PHONY: test-unit
test-unit:  ## Run only unit tests
	@echo "🧪 Running unit tests..."
	pytest -m unit

.PHONY: test-integration
test-integration:  ## Run only integration tests
	@echo "🧪 Running integration tests..."
	pytest -m integration

.PHONY: test-watch
test-watch:  ## Run tests in watch mode
	@echo "👀 Watching for changes..."
	pytest-watch

.PHONY: test-parallel
test-parallel:  ## Run tests in parallel
	@echo "🚀 Running tests in parallel..."
	pytest -n auto

.PHONY: test-verbose
test-verbose:  ## Run tests with verbose output
	@echo "🧪 Running verbose tests..."
	pytest -vv

.PHONY: coverage
coverage:  ## Generate coverage report
	@echo "📊 Generating coverage report..."
	pytest --cov=src --cov-report=html --cov-report=term
	@echo "✅ Coverage report generated in htmlcov/"

.PHONY: coverage-open
coverage-open: coverage  ## Generate and open coverage report
	@echo "🌐 Opening coverage report..."
	python -m webbrowser htmlcov/index.html

# ============================================================================
# Bot Operations
# ============================================================================

.PHONY: run
run:  ## Run the Discord bot
	@echo "🤖 Starting Discord RAG Bot..."
	python bot.py

.PHONY: load
load:  ## Load documents into vector store
	@echo "📚 Loading documents..."
	python load.py

.PHONY: stats
stats:  ## Show knowledge base statistics
	@echo "📊 Knowledge base statistics:"
	python -m src.cli stats

# ============================================================================
# Database Operations
# ============================================================================

.PHONY: db-migrate
db-migrate:  ## Run database migrations
	@echo "🔄 Running migrations..."
	@echo "Connect to Supabase and run:"
	@echo "  psql -h your-url.supabase.co -U postgres -d postgres -f migrations/001_enhanced_schema.sql"
	@echo "  psql -h your-url.supabase.co -U postgres -d postgres -f migrations/002_row_level_security.sql"
	@echo "  psql -h your-url.supabase.co -U postgres -d postgres -f migrations/003_document_control_system.sql"

.PHONY: db-validate
db-validate:  ## Validate database schema
	@echo "✅ Validating database schema..."
	@echo "Connect to Supabase and run:"
	@echo "  psql -h your-url.supabase.co -U postgres -d postgres -f migrations/validate.sql"

# ============================================================================
# Documentation
# ============================================================================

.PHONY: docs
docs:  ## Build documentation
	@echo "📚 Building documentation..."
	mkdocs build

.PHONY: docs-serve
docs-serve:  ## Serve documentation locally
	@echo "🌐 Serving documentation at http://127.0.0.1:8000"
	mkdocs serve

.PHONY: docs-deploy
docs-deploy:  ## Deploy documentation to GitHub Pages
	@echo "🚀 Deploying documentation..."
	mkdocs gh-deploy

# ============================================================================
# Cleaning
# ============================================================================

.PHONY: clean
clean:  ## Remove build artifacts and cache
	@echo "🧹 Cleaning up..."
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete
	find . -type f -name "*.pyo" -delete
	find . -type f -name "*.pyd" -delete
	find . -type d -name "*.egg-info" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name "*.egg" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name ".pytest_cache" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name ".mypy_cache" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name ".ruff_cache" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name "htmlcov" -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name ".coverage" -delete
	find . -type f -name "coverage.xml" -delete
	rm -rf build/ dist/ 2>/dev/null || true
	@echo "✅ Cleanup complete!"

.PHONY: clean-logs
clean-logs:  ## Remove log files
	@echo "🧹 Cleaning logs..."
	rm -rf logs/*.log logs/*.log.*
	@echo "✅ Logs cleaned!"

.PHONY: clean-all
clean-all: clean clean-logs  ## Remove all generated files
	@echo "✅ Deep clean complete!"

# ============================================================================
# Pre-commit
# ============================================================================

.PHONY: pre-commit
pre-commit:  ## Run pre-commit hooks on all files
	@echo "🔍 Running pre-commit hooks..."
	pre-commit run --all-files

.PHONY: pre-commit-update
pre-commit-update:  ## Update pre-commit hooks
	@echo "⬆️  Updating pre-commit hooks..."
	pre-commit autoupdate

# ============================================================================
# Docker Operations
# ============================================================================

.PHONY: docker-build
docker-build:  ## Build Docker image with build script
	@./scripts/build.sh

.PHONY: docker-build-quick
docker-build-quick:  ## Quick Docker build without cache
	@echo "🐳 Building Docker image (no cache)..."
	docker build --no-cache -t discord-rag-bot:latest .

.PHONY: docker-run
docker-run:  ## Run bot in Docker container
	@echo "🐳 Running bot in Docker..."
	docker run --rm --env-file .env discord-rag-bot:latest

.PHONY: docker-shell
docker-shell:  ## Open shell in Docker container
	@echo "🐳 Opening shell in container..."
	docker run -it --rm --env-file .env --entrypoint /bin/bash discord-rag-bot:latest

.PHONY: docker-scan
docker-scan:  ## Scan Docker image for vulnerabilities
	@echo "🔒 Scanning image for vulnerabilities..."
	@if command -v trivy &> /dev/null; then \
		trivy image discord-rag-bot:latest; \
	else \
		echo "⚠️  Trivy not installed. Install with: brew install trivy"; \
	fi

.PHONY: docker-compose-up
docker-compose-up:  ## Start services with docker-compose (dev)
	@echo "🐳 Starting services..."
	docker-compose up -d

.PHONY: docker-compose-prod
docker-compose-prod:  ## Start services with docker-compose (production)
	@echo "🐳 Starting production services..."
	docker-compose -f docker-compose.prod.yml up -d

.PHONY: docker-compose-down
docker-compose-down:  ## Stop services with docker-compose
	@echo "🐳 Stopping services..."
	docker-compose down

.PHONY: docker-compose-logs
docker-compose-logs:  ## Show docker-compose logs
	docker-compose logs -f bot

.PHONY: docker-compose-restart
docker-compose-restart:  ## Restart docker-compose services
	@echo "🔄 Restarting services..."
	docker-compose restart

.PHONY: docker-stats
docker-stats:  ## Show Docker container resource usage
	@docker stats --format "table {{.Container}}\t{{.CPUPerc}}\t{{.MemUsage}}\t{{.NetIO}}"

# ============================================================================
# Kubernetes Operations
# ============================================================================

.PHONY: k8s-deploy
k8s-deploy:  ## Deploy to Kubernetes
	@./scripts/deploy-k8s.sh

.PHONY: k8s-status
k8s-status:  ## Show Kubernetes deployment status
	@kubectl get all -n discord-rag-bot

.PHONY: k8s-logs
k8s-logs:  ## Show Kubernetes logs
	@kubectl logs -n discord-rag-bot -l app=discord-rag-bot -f

.PHONY: k8s-shell
k8s-shell:  ## Open shell in Kubernetes pod
	@kubectl exec -it -n discord-rag-bot $$(kubectl get pods -n discord-rag-bot -l app=discord-rag-bot -o jsonpath='{.items[0].metadata.name}') -- /bin/bash

.PHONY: k8s-delete
k8s-delete:  ## Delete Kubernetes deployment
	@echo "⚠️  This will delete the deployment!"
	@kubectl delete -f k8s/deployment.yaml
	@kubectl delete -f k8s/hpa.yaml

# ============================================================================
# Environment
# ============================================================================

.PHONY: env-example
env-example:  ## Create .env from .env.example
	@if [ ! -f .env ]; then \
		cp .env.example .env; \
		echo "✅ Created .env from .env.example"; \
		echo "⚠️  Please edit .env and add your API keys!"; \
	else \
		echo "⚠️  .env already exists!"; \
	fi

.PHONY: env-check
env-check:  ## Check if required environment variables are set
	@echo "🔍 Checking environment variables..."
	@python -c "from src.config import get_settings; get_settings(); print('✅ All environment variables are set!')"

# ============================================================================
# Profiling
# ============================================================================

.PHONY: profile
profile:  ## Profile the bot
	@echo "📊 Profiling bot..."
	py-spy record -o profile.svg -- python bot.py

.PHONY: memory-profile
memory-profile:  ## Profile memory usage
	@echo "📊 Profiling memory..."
	python -m memory_profiler bot.py

# ============================================================================
# Release
# ============================================================================

.PHONY: version
version:  ## Show current version
	@python -c "from pyproject import __version__; print(f'Version: {__version__}')"

.PHONY: release-patch
release-patch:  ## Create a patch release (0.0.X)
	@echo "🚀 Creating patch release..."
	semantic-release version --patch

.PHONY: release-minor
release-minor:  ## Create a minor release (0.X.0)
	@echo "🚀 Creating minor release..."
	semantic-release version --minor

.PHONY: release-major
release-major:  ## Create a major release (X.0.0)
	@echo "🚀 Creating major release..."
	semantic-release version --major

# ============================================================================
# Development Shortcuts
# ============================================================================

.PHONY: dev
dev: clean format lint test  ## Run full development cycle
	@echo "✅ Development cycle complete!"

.PHONY: ci
ci: install-dev check coverage  ## Simulate CI pipeline locally
	@echo "✅ CI simulation complete!"

.PHONY: quick-check
quick-check: format lint-fix test-fast  ## Quick check before commit
	@echo "✅ Quick check complete!"

# ============================================================================
# Git Operations
# ============================================================================

.PHONY: git-clean
git-clean:  ## Clean git repository (removes untracked files)
	@echo "⚠️  This will remove all untracked files!"
	@read -p "Are you sure? [y/N] " -n 1 -r; \
	echo; \
	if [[ $$REPLY =~ ^[Yy]$$ ]]; then \
		git clean -fdx; \
		echo "✅ Repository cleaned!"; \
	fi

# ============================================================================
# System Information
# ============================================================================

.PHONY: info
info:  ## Show project information
	@echo "==========================================

="
	@echo "Discord RAG Bot - Project Information"
	@echo "============================================"
	@echo "Python Version: $$(python --version)"
	@echo "Pip Version: $$(pip --version)"
	@echo "Git Branch: $$(git branch --show-current)"
	@echo "Git Commit: $$(git rev-parse --short HEAD)"
	@echo "Project Root: $$(pwd)"
	@echo "============================================"

# ============================================================================
# Default Target
# ============================================================================

.DEFAULT_GOAL := help
