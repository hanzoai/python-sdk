.DEFAULT_GOAL := all
SHELL := /bin/bash
.PHONY: help all setup install install-local uninstall install-python venv deps test lint format build clean publish-all check check-forbidden check-functions test-no-stubs test-all security install-hooks

# Colors for output
CYAN := \033[0;36m
GREEN := \033[0;32m
RED := \033[0;31m
YELLOW := \033[0;33m
NC := \033[0m # No Color

# Python version
PYTHON_VERSION := 3.12

help: ## Show this help message
	@echo -e "$(CYAN)Hanzo Python SDK Monorepo Makefile$(NC)"
	@echo -e "$(YELLOW)Usage:$(NC) make [target]"
	@echo
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "  $(GREEN)%-20s$(NC) %s\n", $$1, $$2}'

all: format lint test ## Run all checks

# ==================== INSTALLATION ====================
# Install CLI tools to ~/.local/bin/ (like Claude Code)

INSTALL_DIR := $(HOME)/.local/bin

install: ## Install CLI tools to ~/.local/bin via uv tool
	@echo -e "$(CYAN)Installing Hanzo CLI tools to $(INSTALL_DIR)...$(NC)"
	@if ! command -v uv &> /dev/null; then \
		echo -e "$(RED)Error: uv is not installed. Run: curl -LsSf https://astral.sh/uv/install.sh | sh$(NC)"; \
		exit 1; \
	fi
	@uv tool install hanzo --upgrade 2>/dev/null || uv tool install hanzo
	@uv tool install hanzo-mcp --upgrade 2>/dev/null || uv tool install hanzo-mcp
	@uv tool install hanzo-agents --upgrade 2>/dev/null || uv tool install hanzo-agents
	@echo ""
	@echo -e "$(GREEN)✓ Hanzo CLI tools installed!$(NC)"
	@echo -e "  Location: $(INSTALL_DIR)"
	@echo ""
	@echo -e "  $(CYAN)hanzo --help$(NC)        # CLI commands"
	@echo -e "  $(CYAN)hanzo-mcp$(NC)           # MCP server"
	@echo -e "  $(CYAN)hanzo-agents$(NC)        # Agents framework"
	@echo ""
	@if [[ ":$$PATH:" != *":$(INSTALL_DIR):"* ]]; then \
		echo -e "$(YELLOW)Add to PATH:$(NC) export PATH=\"$(INSTALL_DIR):\$$PATH\""; \
	fi

install-local: build ## Install from local source (development)
	@echo -e "$(CYAN)Installing Hanzo from local source...$(NC)"
	@uv tool install --force ./pkg/hanzo
	@uv tool install --force ./pkg/hanzo-mcp
	@uv tool install --force ./pkg/hanzo-agents
	@echo -e "$(GREEN)✓ Installed from local source$(NC)"

uninstall: ## Remove all Hanzo CLI tools
	@echo -e "$(CYAN)Uninstalling Hanzo CLI tools...$(NC)"
	@uv tool uninstall hanzo 2>/dev/null || true
	@uv tool uninstall hanzo-mcp 2>/dev/null || true
	@uv tool uninstall hanzo-agents 2>/dev/null || true
	@echo -e "$(GREEN)✓ Hanzo CLI tools uninstalled$(NC)"

doctor: ## Show installed Hanzo tools
	@echo -e "$(CYAN)Hanzo CLI Tools Status$(NC)"
	@echo ""
	@echo -e "  $(CYAN)uv tools:$(NC)"
	@uv tool list 2>/dev/null | grep -E "^hanzo" | while read line; do \
		name=$$(echo "$$line" | awk '{print $$1}'); \
		ver=$$(echo "$$line" | awk '{print $$2}'); \
		path=$$(command -v "$$name" 2>/dev/null || echo "~/.local/bin/$$name"); \
		printf "    $(GREEN)✓$(NC) %-16s %-10s %s\n" "$$name" "$$ver" "$$path"; \
	done || echo -e "    $(RED)(none installed)$(NC)"
	@echo ""

setup: install-python venv deps ## Complete setup: install Python, create venv, install deps

install-python: ## Install Python using uv
	@echo -e "$(CYAN)Installing Python $(PYTHON_VERSION)...$(NC)"
	@if ! command -v uv &> /dev/null; then \
		echo -e "$(RED)Error: uv is not installed. Please install it first.$(NC)"; \
		echo "Run: curl -LsSf https://astral.sh/uv/install.sh | sh"; \
		exit 1; \
	fi
	@uv python install $(PYTHON_VERSION)
	@echo -e "$(GREEN)Python $(PYTHON_VERSION) installed successfully$(NC)"

venv: ## Create virtual environment
	@echo -e "$(CYAN)Creating virtual environment...$(NC)"
	@uv venv --python $(PYTHON_VERSION)
	@echo -e "$(GREEN)Virtual environment created$(NC)"
	@echo -e "$(YELLOW)Activate with: source .venv/bin/activate$(NC)"

deps: ## Install all dependencies for all packages
	@echo -e "$(CYAN)Installing dependencies...$(NC)"
	@source .venv/bin/activate && uv pip install -e .
	@source .venv/bin/activate && uv pip install -e ./pkg/hanzo-agents
	@source .venv/bin/activate && uv pip install -e ./pkg/hanzo-mcp
	@source .venv/bin/activate && uv pip install -e ./pkg/hanzo
	@source .venv/bin/activate && uv pip install -e ./pkg/hanzo-repl
	@source .venv/bin/activate && uv pip install -e ./pkg/hanzo-memory
	@source .venv/bin/activate && uv pip install -e ./pkg/hanzo-network
	
	@source .venv/bin/activate && uv pip install -e ./pkg/hanzo-aci
	@echo -e "$(GREEN)All dependencies installed$(NC)"

dev-deps: ## Install development dependencies
	@echo -e "$(CYAN)Installing development dependencies...$(NC)"
	@source .venv/bin/activate && uv pip install pytest pytest-asyncio mypy ruff black coverage
	@echo -e "$(GREEN)Development dependencies installed$(NC)"

test: ## Run tests for all packages
	@echo -e "$(CYAN)Running tests...$(NC)"
	@source .venv/bin/activate && PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 python -m pytest tests/ -v
	@source .venv/bin/activate && cd pkg/hanzo-agents && PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 python -m pytest tests/ -v || true
	@source .venv/bin/activate && cd pkg/hanzo-mcp && PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 python -m pytest tests/ -v || true
	@source .venv/bin/activate && cd pkg/hanzo-memory && PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 python -m pytest tests/ -v || true
	@source .venv/bin/activate && cd pkg/hanzo-aci && PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 python -m pytest tests/ -v || true
	@echo -e "$(GREEN)Tests completed$(NC)"

lint: ## Run linting for all packages
	@echo -e "$(CYAN)Running linters...$(NC)"
	@source .venv/bin/activate && ruff check . --fix --quiet
	@source .venv/bin/activate && mypy . --ignore-missing-imports --no-error-summary 2>/dev/null || true
	@echo -e "$(GREEN)Linting completed$(NC)"

format: ## Format code for all packages
	@echo -e "$(CYAN)Formatting code...$(NC)"
	@source .venv/bin/activate && ruff format . --quiet
	@source .venv/bin/activate && black . --quiet 2>/dev/null || true
	@echo -e "$(GREEN)Formatting completed$(NC)"

build: ## Build all packages
	@echo -e "$(CYAN)Building packages...$(NC)"
	@uv build .
	@cd pkg/hanzo-agents && uv build
	@cd pkg/hanzo-mcp && uv build
	@cd pkg/hanzo && uv build
	@cd pkg/hanzo-repl && uv build
	@cd pkg/hanzo-memory && uv build
	@cd pkg/hanzo-network && uv build
	@cd pkg/hanzo-aci && uv build
	@echo -e "$(GREEN)All packages built$(NC)"

clean: ## Clean build artifacts
	@echo -e "$(CYAN)Cleaning build artifacts...$(NC)"
	@find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	@find . -type d -name "*.egg-info" -exec rm -rf {} + 2>/dev/null || true
	@find . -type d -name "dist" -exec rm -rf {} + 2>/dev/null || true
	@find . -type d -name "build" -exec rm -rf {} + 2>/dev/null || true
	@find . -type d -name ".pytest_cache" -exec rm -rf {} + 2>/dev/null || true
	@find . -type d -name ".mypy_cache" -exec rm -rf {} + 2>/dev/null || true
	@find . -type d -name ".ruff_cache" -exec rm -rf {} + 2>/dev/null || true
	@find . -type f -name "*.pyc" -delete 2>/dev/null || true
	@find . -type f -name "*.pyo" -delete 2>/dev/null || true
	@find . -type f -name ".coverage" -delete 2>/dev/null || true
	@rm -rf htmlcov/ 2>/dev/null || true
	@echo -e "$(GREEN)Clean completed$(NC)"

publish-check: ## Check if packages are ready to publish
	@echo -e "$(CYAN)Checking package configurations...$(NC)"
	@python scripts/check_packages.py

publish-all: build ## Publish all packages to PyPI
	@echo -e "$(CYAN)Publishing packages to PyPI...$(NC)"
	@echo -e "$(YELLOW)Warning: This will publish to PyPI. Make sure you have the correct credentials.$(NC)"
	@read -p "Continue? [y/N] " -n 1 -r; echo; \
	if [[ $$REPLY =~ ^[Yy]$$ ]]; then \
		$(MAKE) publish-hanzoai; \
		$(MAKE) publish-hanzo-agents; \
		$(MAKE) publish-hanzo-mcp; \
		$(MAKE) publish-hanzo; \
		$(MAKE) publish-hanzo-repl; \
		$(MAKE) publish-hanzo-memory; \
		$(MAKE) publish-hanzo-network; \
		$(MAKE) publish-hanzo-aci; \
	else \
		echo -e "$(RED)Publishing cancelled$(NC)"; \
	fi

# Publishing individual packages
publish-hanzoai: ## Publish hanzoai package
	@echo -e "$(CYAN)Publishing hanzoai...$(NC)"
	@cd . && TWINE_USERNAME=__token__ TWINE_PASSWORD=$${PYPI_TOKEN} twine upload dist/* --skip-existing

publish-hanzo-agents: ## Publish hanzo-agents package  
	@echo -e "$(CYAN)Publishing hanzo-agents...$(NC)"
	@cd pkg/hanzo-agents && TWINE_USERNAME=__token__ TWINE_PASSWORD=$${PYPI_TOKEN} twine upload dist/* --skip-existing

publish-hanzo-mcp: check ## Publish hanzo-mcp package (REQUIRES ALL CHECKS TO PASS)
	@echo -e "$(CYAN)Publishing hanzo-mcp...$(NC)"
	@cd pkg/hanzo-mcp && TWINE_USERNAME=__token__ TWINE_PASSWORD=$${PYPI_TOKEN} twine upload dist/* --skip-existing

publish-hanzo: ## Publish hanzo package
	@echo -e "$(CYAN)Publishing hanzo...$(NC)"
	@cd pkg/hanzo && TWINE_USERNAME=__token__ TWINE_PASSWORD=$${PYPI_TOKEN} twine upload dist/* --skip-existing

publish-hanzo-repl: ## Publish hanzo-repl package
	@echo -e "$(CYAN)Publishing hanzo-repl...$(NC)"
	@cd pkg/hanzo-repl && TWINE_USERNAME=__token__ TWINE_PASSWORD=$${PYPI_TOKEN} twine upload dist/* --skip-existing

publish-hanzo-memory: ## Publish hanzo-memory package
	@echo -e "$(CYAN)Publishing hanzo-memory...$(NC)"
	@cd pkg/hanzo-memory && TWINE_USERNAME=__token__ TWINE_PASSWORD=$${PYPI_TOKEN} twine upload dist/* --skip-existing

publish-hanzo-network: ## Publish hanzo-network package
	@echo -e "$(CYAN)Publishing hanzo-network...$(NC)"
	@cd pkg/hanzo-network && TWINE_USERNAME=__token__ TWINE_PASSWORD=$${PYPI_TOKEN} twine upload dist/* --skip-existing



publish-hanzo-aci: ## Publish hanzo-aci as dev-aci package
	@echo -e "$(CYAN)Publishing hanzo-aci as dev-aci...$(NC)"
	@cd pkg/hanzo-aci && TWINE_USERNAME=__token__ TWINE_PASSWORD=$${PYPI_TOKEN} twine upload dist/* --skip-existing

# Individual package commands
test-hanzoai: ## Test main hanzoai package
	@source .venv/bin/activate && python -m pytest tests/ -v

test-agents: ## Test hanzo-agents package
	@source .venv/bin/activate && cd pkg/hanzo-agents && python -m pytest tests/ -v

test-mcp: ## Test hanzo-mcp package
	@source .venv/bin/activate && cd pkg/hanzo-mcp && python -m pytest tests/ -v

test-memory: ## Test hanzo-memory package
	@source .venv/bin/activate && cd pkg/hanzo-memory && python -m pytest tests/ -v

test-aci: ## Test hanzo-aci package
	@source .venv/bin/activate && cd pkg/hanzo-aci && python -m pytest tests/ -v

# Development helpers
shell: ## Start Python shell with packages loaded
	@source .venv/bin/activate && python

watch-tests: ## Watch and run tests on file changes
	@source .venv/bin/activate && watchmedo shell-command \
		--patterns="*.py" \
		--recursive \
		--command='make test' \
		.

update-deps: ## Update all dependencies to latest versions
	@echo -e "$(CYAN)Updating dependencies...$(NC)"
	@source .venv/bin/activate && uv pip compile pyproject.toml -o requirements.txt --upgrade
	@source .venv/bin/activate && uv pip sync requirements.txt
	@echo -e "$(GREEN)Dependencies updated$(NC)"

check-types: ## Run type checking
	@echo -e "$(CYAN)Running type checks...$(NC)"
	@source .venv/bin/activate && mypy pkg/hanzoai --ignore-missing-imports
	@source .venv/bin/activate && pyright pkg/hanzoai || true
	@echo -e "$(GREEN)Type checking completed$(NC)"

coverage: ## Run tests with coverage
	@echo -e "$(CYAN)Running tests with coverage...$(NC)"
	@source .venv/bin/activate && PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 coverage run -m pytest tests/
	@source .venv/bin/activate && coverage report
	@source .venv/bin/activate && coverage html
	@echo -e "$(GREEN)Coverage report generated in htmlcov/$(NC)"

# ==================== STRICT QUALITY GATES ====================

install-hooks: ## Install pre-commit hooks to catch issues locally
	@echo -e "$(GREEN)Installing pre-commit hooks...$(NC)"
	@pip install pre-commit
	@pre-commit install
	@pre-commit install --hook-type pre-push
	@echo -e "$(GREEN)✅ Pre-commit hooks installed!$(NC)"

check-forbidden: ## Check for TODO/STUB/FAKE patterns (BLOCKS DEPLOYMENT)
	@echo -e "$(YELLOW)Checking for TODO/STUB/FAKE patterns...$(NC)"
	@! grep -r "TODO\|STUB\|FAKE\|UNFINISHED\|HACK\|XXX\|NotImplementedError" \
		--include="*.py" \
		--exclude-dir=test \
		--exclude-dir=.git \
		--exclude-dir=build \
		--exclude-dir=dist \
		pkg/hanzo-mcp 2>/dev/null || (echo -e "$(RED)❌ FORBIDDEN PATTERNS FOUND! Remove them!$(NC)" && exit 1)
	@echo -e "$(GREEN)✅ No forbidden patterns$(NC)"

check-functions: ## Check for empty/stub functions (BLOCKS DEPLOYMENT)
	@echo -e "$(YELLOW)Checking for empty functions...$(NC)"
	@python scripts/check_empty_functions.py
	@echo -e "$(GREEN)✅ All functions implemented$(NC)"

test-no-stubs: ## Run anti-stub tests (BLOCKS DEPLOYMENT)
	@echo -e "$(YELLOW)Running anti-stub tests...$(NC)"
	@source .venv/bin/activate && cd pkg/hanzo-mcp && python -m pytest tests/test_no_stubs.py -v
	@echo -e "$(GREEN)✅ No stubs found$(NC)"

test-all: ## Run ALL tests - NO SKIPS ALLOWED (BLOCKS DEPLOYMENT)
	@echo -e "$(YELLOW)Running ALL tests (no skips allowed)...$(NC)"
	@source .venv/bin/activate && cd pkg/hanzo-mcp && python -m pytest tests/ \
		-v \
		--strict-markers \
		--tb=short \
		--maxfail=1 \
		-x \
		2>&1 | tee test-output.log
	@if grep -q "SKIPPED" test-output.log; then \
		echo -e "$(RED)❌ TESTS WERE SKIPPED! Fix or remove them!$(NC)"; \
		exit 1; \
	fi
	@if grep -q "FAILED" test-output.log; then \
		echo -e "$(RED)❌ TESTS FAILED! All tests must pass!$(NC)"; \
		exit 1; \
	fi
	@rm -f test-output.log
	@echo -e "$(GREEN)✅ All tests passed!$(NC)"

security: ## Security scan with bandit (BLOCKS DEPLOYMENT)
	@echo -e "$(YELLOW)Security scanning...$(NC)"
	@source .venv/bin/activate && bandit -r pkg/hanzo-mcp/hanzo_mcp -ll
	@echo -e "$(GREEN)✅ Security scan passed$(NC)"

# MASTER CHECK - Runs ALL quality gates (REQUIRED BEFORE DEPLOYMENT)
check: check-forbidden check-functions lint test-no-stubs test-all security
	@echo -e "$(GREEN)════════════════════════════════════════$(NC)"
	@echo -e "$(GREEN)✅ ALL QUALITY CHECKS PASSED!$(NC)"
	@echo -e "$(GREEN)✅ NO TODOs, STUBs, or FAKE code found$(NC)"
	@echo -e "$(GREEN)✅ All tests are passing$(NC)"
	@echo -e "$(GREEN)✅ All functions are implemented$(NC)"
	@echo -e "$(GREEN)🚀 Code is ready for deployment!$(NC)"
	@echo -e "$(GREEN)════════════════════════════════════════$(NC)"
