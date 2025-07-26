# Hanzo Memory Service Makefile

# Colors
BLUE := \033[0;34m
GREEN := \033[0;32m
YELLOW := \033[0;33m
RED := \033[0;31m
NC := \033[0m # No Color

# Python version
PYTHON_VERSION := 3.11

# Project paths
PROJECT_ROOT := $(shell pwd)
SRC_DIR := src
TEST_DIR := tests
DATA_DIR := data
INFINITY_DB_PATH := $(DATA_DIR)/infinity_db

# Default target
.DEFAULT_GOAL := help

# Help
.PHONY: help
help: ## Show this help message
	@echo "$(BLUE)Hanzo Memory Service$(NC)"
	@echo "$(GREEN)Available commands:$(NC)"
	@awk 'BEGIN {FS = ":.*##"; printf "\n"} /^[a-zA-Z_-]+:.*?##/ { printf "  $(YELLOW)%-15s$(NC) %s\n", $$1, $$2 } /^##@/ { printf "\n$(BLUE)%s$(NC)\n", substr($$0, 5) }' $(MAKEFILE_LIST)

##@ Setup

.PHONY: install-python
install-python: ## Install Python using uv
	@echo "$(BLUE)Installing Python $(PYTHON_VERSION)...$(NC)"
	@command -v uv >/dev/null 2>&1 || (echo "Installing uv..." && curl -LsSf https://astral.sh/uv/install.sh | sh)
	uv python install $(PYTHON_VERSION)

.PHONY: venv
venv: ## Create virtual environment using uv
	@echo "$(BLUE)Creating virtual environment...$(NC)"
	uv venv

.PHONY: install
install: ## Install dependencies
	@echo "$(BLUE)Installing dependencies...$(NC)"
	uv pip install -e ".[dev,test,docs]"

.PHONY: setup
setup: venv install dirs ## Complete project setup
	@echo "$(GREEN)Setup complete!$(NC)"

.PHONY: dirs
dirs: ## Create necessary directories
	@echo "$(BLUE)Creating directories...$(NC)"
	@mkdir -p $(DATA_DIR)
	@mkdir -p $(INFINITY_DB_PATH)
	@mkdir -p logs
	@mkdir -p $(SRC_DIR)/hanzo_memory
	@mkdir -p $(TEST_DIR)

##@ Development

.PHONY: dev
dev: ## Run development server
	@echo "$(BLUE)Starting development server...$(NC)"
	uv run uvicorn hanzo_memory.server:app --reload --host 0.0.0.0 --port 4000

.PHONY: mcp
mcp: ## Run MCP server
	@echo "$(BLUE)Starting MCP server...$(NC)"
	uv run hanzo-memory-mcp

.PHONY: install-mcp
install-mcp: ## Install MCP server to Claude Desktop
	@echo "$(BLUE)Installing MCP server to Claude Desktop...$(NC)"
	@echo "Add the following to your Claude Desktop config:"
	@echo '  "mcpServers": {'
	@echo '    "hanzo-memory": {'
	@echo '      "command": "uv",'
	@echo '      "args": ["run", "hanzo-memory-mcp"],'
	@echo '      "cwd": "$(shell pwd)"'
	@echo '    }'
	@echo '  }'

.PHONY: run
run: ## Run production server
	@echo "$(BLUE)Starting production server...$(NC)"
	uv run uvicorn hanzo_memory.server:app --host 0.0.0.0 --port 4000

##@ Testing

.PHONY: test
test: ## Run tests
	@echo "$(BLUE)Running tests...$(NC)"
	uv run pytest -v

.PHONY: test-cov
test-cov: ## Run tests with coverage
	@echo "$(BLUE)Running tests with coverage...$(NC)"
	uv run pytest --cov=hanzo_memory --cov-report=html --cov-report=term

.PHONY: test-watch
test-watch: ## Run tests in watch mode
	@echo "$(BLUE)Running tests in watch mode...$(NC)"
	uv run pytest-watch

##@ Code Quality

.PHONY: lint
lint: ## Run linting
	@echo "$(BLUE)Running ruff linter...$(NC)"
	uv run ruff check $(SRC_DIR) $(TEST_DIR)

.PHONY: format
format: ## Format code
	@echo "$(BLUE)Formatting code...$(NC)"
	uv run ruff format $(SRC_DIR) $(TEST_DIR)

.PHONY: type-check
type-check: ## Run type checking
	@echo "$(BLUE)Running type checker...$(NC)"
	uv run mypy $(SRC_DIR)

.PHONY: check
check: lint type-check test ## Run all checks

##@ Build & Package

.PHONY: build
build: clean check ## Build package
	@echo "$(BLUE)Building package...$(NC)"
	uv build

.PHONY: install-local
install-local: ## Install package locally with uv
	@echo "$(BLUE)Installing package locally...$(NC)"
	uv pip install .

.PHONY: publish
publish: build ## Build and publish package to PyPI
	@echo "$(BLUE)Publishing package to PyPI...$(NC)"
	uv run twine upload dist/*

##@ Database

.PHONY: db-init
db-init: ## Initialize InfinityDB
	@echo "$(BLUE)Initializing InfinityDB...$(NC)"
	uv run python -m hanzo_memory.db.init

.PHONY: db-reset
db-reset: ## Reset InfinityDB (WARNING: destroys all data)
	@echo "$(RED)WARNING: This will destroy all data!$(NC)"
	@read -p "Are you sure? [y/N] " -n 1 -r; \
	echo; \
	if [[ $$REPLY =~ ^[Yy]$$ ]]; then \
		rm -rf $(INFINITY_DB_PATH)/*; \
		$(MAKE) db-init; \
	fi

##@ Documentation

.PHONY: docs
docs: ## Build documentation
	@echo "$(BLUE)Building documentation...$(NC)"
	uv run mkdocs build

.PHONY: docs-serve
docs-serve: ## Serve documentation locally
	@echo "$(BLUE)Serving documentation...$(NC)"
	uv run mkdocs serve

##@ Cleanup

.PHONY: clean
clean: ## Clean build artifacts
	@echo "$(BLUE)Cleaning build artifacts...$(NC)"
	@rm -rf build dist *.egg-info
	@rm -rf .pytest_cache .ruff_cache .mypy_cache
	@rm -rf htmlcov .coverage coverage.xml
	@find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	@find . -type f -name "*.pyc" -delete

.PHONY: clean-all
clean-all: clean ## Clean everything including data
	@echo "$(RED)Cleaning all data...$(NC)"
	@rm -rf $(DATA_DIR)
	@rm -rf logs

##@ Docker (Optional)

.PHONY: docker-build
docker-build: ## Build Docker image
	@echo "$(BLUE)Building Docker image...$(NC)"
	docker build -t hanzo-memory:latest .

.PHONY: docker-run
docker-run: ## Run Docker container
	@echo "$(BLUE)Running Docker container...$(NC)"
	docker run -p 4000:4000 -v $(PWD)/data:/app/data hanzo-memory:latest

##@ Default target

.PHONY: all
all: setup build test ## Run setup, build, and test

# Make default target
.DEFAULT: help