# AgentROS Development Makefile
# Optimized commands for efficient local development

.PHONY: help setup quick-setup test test-fast test-unit test-integration clean dev-server format lint type-check install build docs

# Default target
.DEFAULT_GOAL := help

# Colors for output
BLUE=\033[0;34m
GREEN=\033[0;32m
YELLOW=\033[1;33m
RED=\033[0;31m
NC=\033[0m # No Color

# Configuration
PYTHON := python3
PIP := pip
PYTEST := pytest
PARALLEL_WORKERS := $(shell nproc --ignore=1)

help: ## Show this help message
	@echo "$(BLUE)🤖 AgentROS Development Commands$(NC)"
	@echo ""
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "$(GREEN)%-20s$(NC) %s\n", $$1, $$2}'

# Setup commands
setup: ## Full development setup (includes system optimizations)
	@echo "$(BLUE)🚀 Running full development setup...$(NC)"
	@./scripts/setup_dev.sh setup

quick-setup: ## Quick development setup (no system changes)
	@echo "$(BLUE)⚡ Running quick development setup...$(NC)"
	@./scripts/setup_dev.sh quick

install: ## Install package in development mode
	@echo "$(BLUE)📦 Installing AgentROS in development mode...$(NC)"
	@$(PIP) install -e ".[dev]" --quiet

# Testing commands (optimized for speed)
test: ## Run all tests
	@echo "$(BLUE)🧪 Running all tests...$(NC)"
	@$(PYTEST) tests/ -v

test-fast: ## Run fast unit tests only
	@echo "$(BLUE)⚡ Running fast unit tests...$(NC)"
	@$(PYTEST) tests/ -m "unit and not slow" --maxfail=3 -x --tb=short

test-unit: ## Run unit tests with coverage
	@echo "$(BLUE)🔬 Running unit tests with coverage...$(NC)"
	@$(PYTEST) tests/ -m "unit" --cov=agent_core --cov=mcp_server --cov-report=term-missing

test-integration: ## Run integration tests (slow)
	@echo "$(YELLOW)🔗 Running integration tests (this may take a while)...$(NC)"
	@$(PYTEST) tests/ -m "integration" --run-integration -v

test-perf: ## Run performance tests
	@echo "$(BLUE)📊 Running performance tests...$(NC)"
	@$(PYTEST) tests/ --durations=10 -v -m "not slow"

# Development server commands
dev-server: ## Start development servers (MCP + Ollama check)
	@echo "$(BLUE)🚀 Starting development servers...$(NC)"
	@./scripts/dev_server.sh

mcp-server: ## Start only MCP server
	@echo "$(BLUE)🔧 Starting MCP server...$(NC)"
	@agentros server --host localhost --port 8000

status: ## Check system status
	@echo "$(BLUE)📋 Checking AgentROS system status...$(NC)"
	@agentros status

# Code quality commands (optimized for speed)
format: ## Format code with black and isort
	@echo "$(BLUE)✨ Formatting code...$(NC)"
	@black agent_core/ mcp_server/ tests/ --line-length=88 --quiet
	@isort agent_core/ mcp_server/ tests/ --profile black --quiet

lint: ## Lint code with ruff (fast)
	@echo "$(BLUE)🔍 Linting code...$(NC)"
	@ruff check agent_core/ mcp_server/ tests/ --fix

lint-strict: ## Strict linting without auto-fix
	@echo "$(BLUE)🔍 Strict linting (no auto-fix)...$(NC)"
	@ruff check agent_core/ mcp_server/ tests/

type-check: ## Run type checking with mypy
	@echo "$(BLUE)🏷️  Type checking...$(NC)"
	@mypy agent_core/ mcp_server/ --ignore-missing-imports

pre-commit: ## Run pre-commit hooks
	@echo "$(BLUE)🪝 Running pre-commit hooks...$(NC)"
	@pre-commit run --all-files

# Development workflow commands
dev-check: format lint test-fast ## Quick development check (format + lint + fast tests)
	@echo "$(GREEN)✅ Development check completed!$(NC)"

full-check: format lint type-check test ## Full quality check (all tools + all tests)
	@echo "$(GREEN)✅ Full quality check completed!$(NC)"

# Example usage commands
example-basic: ## Generate a basic ROS 2 package example
	@echo "$(BLUE)📦 Generating basic ROS 2 package example...$(NC)"
	@agentros generate "Create a simple ROS 2 node that publishes hello world messages"

example-service: ## Generate a service example
	@echo "$(BLUE)🔧 Generating service example...$(NC)"
	@agentros generate "Create a service package that handles HTTP requests"

example-complex: ## Generate a complex package example
	@echo "$(BLUE)🏗️  Generating complex package example...$(NC)"
	@agentros generate "Create a web application with authentication and user management"

# Cleanup commands
clean: ## Clean up generated files and caches
	@echo "$(BLUE)🧹 Cleaning up...$(NC)"
	@find . -type f -name "*.pyc" -delete
	@find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	@find . -type d -name "*.egg-info" -exec rm -rf {} + 2>/dev/null || true
	@find . -type d -name ".pytest_cache" -exec rm -rf {} + 2>/dev/null || true
	@find . -type d -name ".mypy_cache" -exec rm -rf {} + 2>/dev/null || true
	@find . -type f -name ".coverage" -delete 2>/dev/null || true
	@rm -rf build/ dist/ 2>/dev/null || true

clean-sandbox: ## Clean MCP sandbox
	@echo "$(BLUE)🧹 Cleaning MCP sandbox...$(NC)"
	@rm -rf /tmp/agentros_sandbox 2>/dev/null || true

# Build and distribution
build: clean ## Build package
	@echo "$(BLUE)📦 Building package...$(NC)"
	@$(PYTHON) -m build

# Resource monitoring
monitor-resources: ## Monitor resource usage during development
	@echo "$(BLUE)📊 Monitoring resource usage...$(NC)"
	@echo "Press Ctrl+C to stop monitoring"
	@while true; do \
		echo "$(YELLOW)Memory:$(NC) $$(free -h | grep Mem | awk '{print $$3 "/" $$2}')  $(YELLOW)CPU:$(NC) $$(top -bn1 | grep "Cpu(s)" | sed "s/.*, *\([0-9.]*\)%* id.*/\1/" | awk '{print 100 - $$1"%"}')  $(YELLOW)Disk:$(NC) $$(df -h . | tail -1 | awk '{print $$5}')"; \
		sleep 2; \
	done

# Git workflow helpers
git-status: ## Show git status with AgentROS context
	@echo "$(BLUE)📊 Git Status$(NC)"
	@git status --short
	@echo ""
	@echo "$(BLUE)Recent commits:$(NC)"
	@git log --oneline -5

commit-ready: dev-check ## Check if ready for commit
	@echo "$(GREEN)✅ Ready for commit!$(NC)"
	@echo "$(BLUE)Next steps:$(NC)"
	@echo "  git add ."
	@echo "  git commit -m 'Your commit message'"

# Documentation
docs: ## Generate documentation
	@echo "$(BLUE)📚 Generating documentation...$(NC)"
	@echo "Documentation generation not yet implemented"

# Performance optimization
optimize: ## Apply performance optimizations
	@echo "$(BLUE)⚡ Applying performance optimizations...$(NC)"
	@echo "Setting Python optimizations..."
	@export PYTHONOPTIMIZE=1
	@echo "$(GREEN)✅ Optimizations applied$(NC)"

# Troubleshooting
diagnose: ## Run system diagnostics
	@echo "$(BLUE)🔍 Running system diagnostics...$(NC)"
	@echo "$(BLUE)Python version:$(NC)"
	@$(PYTHON) --version
	@echo "$(BLUE)Available memory:$(NC)"
	@free -h | grep Mem
	@echo "$(BLUE)CPU cores:$(NC)"
	@nproc
	@echo "$(BLUE)Disk space:$(NC)"
	@df -h . | tail -1
	@echo "$(BLUE)Ollama status:$(NC)"
	@curl -s http://localhost:11434/api/tags > /dev/null && echo "✅ Ollama running" || echo "❌ Ollama not accessible"
	@echo "$(BLUE)MCP server status:$(NC)"
	@curl -s http://localhost:8000/health > /dev/null && echo "✅ MCP server running" || echo "❌ MCP server not accessible"

# =============================================================================
# GLOBAL MEMORY SYSTEM TARGETS
# =============================================================================

.PHONY: memory-setup memory-start memory-stop memory-test memory-clean memory-docs

memory-setup: ## Setup Global Memory MCP Server infrastructure
	@echo "🧠 Setting up Global Memory infrastructure..."
	@if ! command -v docker-compose >/dev/null 2>&1; then \
		echo "❌ docker-compose is required but not installed"; \
		exit 1; \
	fi
	@if ! command -v psql >/dev/null 2>&1; then \
		echo "⚠️  PostgreSQL client recommended for database management"; \
	fi
	@echo "✅ Global Memory setup check complete"

memory-start: memory-setup ## Start Global Memory MCP Server with Docker
	@echo "🚀 Starting Global Memory MCP Server..."
	@docker-compose -f docker-compose.global-memory.yml up -d
	@echo "⏳ Waiting for services to be ready..."
	@sleep 10
	@echo "🧠 Global Memory Server: http://localhost:8001"
	@echo "📊 API Documentation: http://localhost:8001/docs"
	@echo "💾 Database: postgresql://postgres:postgres@localhost:5432/global_memory"

memory-stop: ## Stop Global Memory MCP Server
	@echo "🛑 Stopping Global Memory MCP Server..."
	@docker-compose -f docker-compose.global-memory.yml down

memory-test: ## Run Global Memory system tests
	@echo "🧪 Running Global Memory tests..."
	@$(PYTHON) -m pytest tests/test_global_memory.py -v --tb=short
	@echo "✅ Global Memory tests completed"

memory-dev: ## Start Global Memory server in development mode
	@echo "🔧 Starting Global Memory server in development mode..."
	@if ! pg_isready -h localhost -p 5432 >/dev/null 2>&1; then \
		echo "❌ PostgreSQL is not running. Please start it first."; \
		echo "   Run: sudo systemctl start postgresql"; \
		exit 1; \
	fi
	@./scripts/start_global_memory.sh

memory-clean: ## Clean Global Memory data and containers
	@echo "🧹 Cleaning Global Memory system..."
	@docker-compose -f docker-compose.global-memory.yml down -v
	@docker system prune -f --filter label=com.docker.compose.project=agentros
	@echo "✅ Global Memory cleanup completed"

memory-logs: ## View Global Memory server logs
	@echo "📋 Viewing Global Memory server logs..."
	@docker-compose -f docker-compose.global-memory.yml logs -f global-memory-server

memory-status: ## Check Global Memory server status
	@echo "📊 Checking Global Memory server status..."
	@curl -s http://localhost:8001/health | jq . || echo "❌ Server not responding"
	@curl -s http://localhost:8001/api/statistics | jq . || echo "❌ Statistics not available"

memory-backup: ## Backup Global Memory database
	@echo "💾 Backing up Global Memory database..."
	@mkdir -p backups
	@docker exec gmcp_postgres pg_dump -U postgres global_memory > backups/global_memory_$(shell date +%Y%m%d_%H%M%S).sql
	@echo "✅ Database backup completed"

memory-docs: ## Generate Global Memory documentation
	@echo "📚 Generating Global Memory documentation..."
	@$(PYTHON) -c "from global_mcp_server.core.server import GlobalMCPServer; print('Global Memory MCP Server Documentation')"
	@echo "📖 See GLOBAL_MEMORY_DESIGN.md for architecture details"

# Development workflow shortcuts
dev: install dev-server ## Full development startup (install + start servers)

quick: test-fast lint ## Quick development check

ship: full-check build ## Prepare for shipping (full check + build)

# Show performance tips
perf-tips: ## Show performance optimization tips
	@echo "$(BLUE)⚡ Performance Tips for AgentROS Development$(NC)"
	@echo ""
	@echo "$(GREEN)🚀 Speed up testing:$(NC)"
	@echo "  make test-fast        # Run only fast unit tests"
	@echo "  pytest -x --tb=short  # Stop on first failure, short tracebacks"
	@echo "  pytest -m 'not slow'  # Skip slow tests"
	@echo ""
	@echo "$(GREEN)🧠 Optimize LLM usage:$(NC)"
	@echo "  export AGENTROS_USE_CACHE=true   # Enable response caching"
	@echo "  pytest --mock-llm               # Use mocked LLM for testing"
	@echo ""
	@echo "$(GREEN)💾 Reduce memory usage:$(NC)"
	@echo "  export AGENTROS_PARALLEL_WORKERS=2  # Limit parallel tasks"
	@echo "  make clean                          # Clean up caches"
	@echo ""
	@echo "$(GREEN)⚡ Fast development cycle:$(NC)"
	@echo "  make quick           # Quick lint + test cycle"
	@echo "  make dev-check       # Format + lint + fast test"
	@echo "  make commit-ready    # Full pre-commit check"
