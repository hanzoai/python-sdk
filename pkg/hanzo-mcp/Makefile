# Hanzo MCP Package Makefile
SHELL := /bin/bash

# ANSI color codes
GREEN := \033[0;32m
YELLOW := \033[0;33m
RED := \033[0;31m
BLUE := \033[0;34m
RESET := \033[0m

# Package info
PACKAGE_NAME := hanzo-mcp
CURRENT_VERSION := $(shell grep -E '^version = ' pyproject.toml | sed 's/version = "//g' | sed 's/"//g')

.PHONY: help
help: ## Show this help message
	@printf "$(BLUE)Hanzo MCP Package Commands$(RESET)\n"
	@printf "\n"
	@printf "$(GREEN)Development:$(RESET)\n"
	@printf "  make install     - Install package in development mode\n"
	@printf "  make test        - Run tests\n"
	@printf "  make lint        - Run linting\n"
	@printf "  make format      - Format code\n"
	@printf "\n"
	@printf "$(GREEN)Publishing:$(RESET)\n"
	@printf "  make build       - Build distribution packages\n"
	@printf "  make publish     - Publish to PyPI (requires API token)\n"
	@printf "  make publish-test - Publish to Test PyPI\n"
	@printf "  make version     - Show current version\n"
	@printf "  make bump-patch  - Bump patch version (x.y.Z)\n"
	@printf "  make bump-minor  - Bump minor version (x.Y.0)\n"
	@printf "  make bump-major  - Bump major version (X.0.0)\n"
	@printf "\n"
	@printf "$(GREEN)Current Version:$(RESET) $(CURRENT_VERSION)\n"

# ========== Development Commands ==========

.PHONY: install
install: ## Install package in development mode
	@printf "$(GREEN)Installing hanzo-mcp in development mode...$(RESET)\n"
	@pip install -e ".[dev,test]"
	@printf "$(GREEN)Installation complete!$(RESET)\n"

.PHONY: test
test: ## Run tests
	@printf "$(GREEN)Running tests...$(RESET)\n"
	@python -m pytest -v

.PHONY: test-cov
test-cov: ## Run tests with coverage
	@printf "$(GREEN)Running tests with coverage...$(RESET)\n"
	@python -m pytest --cov=hanzo_mcp --cov-report=html --cov-report=term

.PHONY: lint
lint: ## Run linting
	@printf "$(GREEN)Running ruff linter...$(RESET)\n"
	@ruff check hanzo_mcp/

.PHONY: format
format: ## Format code
	@printf "$(GREEN)Formatting code...$(RESET)\n"
	@ruff format hanzo_mcp/
	@ruff check --fix hanzo_mcp/

.PHONY: type-check
type-check: ## Run type checking
	@printf "$(GREEN)Running type checks...$(RESET)\n"
	@mypy hanzo_mcp/

# ========== Build Commands ==========

.PHONY: clean
clean: ## Clean build artifacts
	@printf "$(YELLOW)Cleaning build artifacts...$(RESET)\n"
	@rm -rf build/ dist/ *.egg-info .pytest_cache .coverage htmlcov
	@find . -type d -name __pycache__ -exec rm -rf {} +
	@printf "$(GREEN)Clean complete!$(RESET)\n"

.PHONY: build
build: clean ## Build distribution packages
	@printf "$(GREEN)Building distribution packages...$(RESET)\n"
	@python -m build
	@printf "$(GREEN)Build complete! Packages in dist/$(RESET)\n"
	@ls -la dist/

# ========== Version Management ==========

.PHONY: version
version: ## Show current version
	@printf "$(GREEN)Current version: $(CURRENT_VERSION)$(RESET)\n"

.PHONY: bump-patch
bump-patch: ## Bump patch version (x.y.Z)
	@printf "$(YELLOW)Bumping patch version...$(RESET)\n"
	@python -c "import re; \
		content = open('pyproject.toml').read(); \
		version = re.search(r'version = \"(.+?)\"', content).group(1); \
		parts = version.split('.'); \
		parts[2] = str(int(parts[2]) + 1); \
		new_version = '.'.join(parts); \
		content = re.sub(r'version = \".+?\"', f'version = \"{new_version}\"', content); \
		open('pyproject.toml', 'w').write(content); \
		print(f'Version bumped from {version} to {new_version}')"
	@printf "$(GREEN)Version updated! Don't forget to commit the change.$(RESET)\n"

.PHONY: bump-minor
bump-minor: ## Bump minor version (x.Y.0)
	@printf "$(YELLOW)Bumping minor version...$(RESET)\n"
	@python -c "import re; \
		content = open('pyproject.toml').read(); \
		version = re.search(r'version = \"(.+?)\"', content).group(1); \
		parts = version.split('.'); \
		parts[1] = str(int(parts[1]) + 1); \
		parts[2] = '0'; \
		new_version = '.'.join(parts); \
		content = re.sub(r'version = \".+?\"', f'version = \"{new_version}\"', content); \
		open('pyproject.toml', 'w').write(content); \
		print(f'Version bumped from {version} to {new_version}')"
	@printf "$(GREEN)Version updated! Don't forget to commit the change.$(RESET)\n"

.PHONY: bump-major
bump-major: ## Bump major version (X.0.0)
	@printf "$(YELLOW)Bumping major version...$(RESET)\n"
	@python -c "import re; \
		content = open('pyproject.toml').read(); \
		version = re.search(r'version = \"(.+?)\"', content).group(1); \
		parts = version.split('.'); \
		parts[0] = str(int(parts[0]) + 1); \
		parts[1] = '0'; \
		parts[2] = '0'; \
		new_version = '.'.join(parts); \
		content = re.sub(r'version = \".+?\"', f'version = \"{new_version}\"', content); \
		open('pyproject.toml', 'w').write(content); \
		print(f'Version bumped from {version} to {new_version}')"
	@printf "$(GREEN)Version updated! Don't forget to commit the change.$(RESET)\n"

# ========== Publishing Commands ==========

.PHONY: check-publish
check-publish: ## Check if ready to publish
	@printf "$(YELLOW)Checking publishing requirements...$(RESET)\n"
	@which twine > /dev/null || (printf "$(RED)Error: twine not installed. Run: pip install twine$(RESET)\n" && exit 1)
	@which python -m build > /dev/null || (printf "$(RED)Error: build not installed. Run: pip install build$(RESET)\n" && exit 1)
	@if [ ! -f ~/.pypirc ]; then \
		printf "$(YELLOW)Warning: ~/.pypirc not found. You'll need to enter credentials manually.$(RESET)\n"; \
	fi
	@printf "$(GREEN)Publishing tools are installed!$(RESET)\n"

.PHONY: publish-test
publish-test: check-publish build ## Publish to Test PyPI
	@printf "$(YELLOW)Publishing to Test PyPI...$(RESET)\n"
	@printf "$(YELLOW)Make sure you have a Test PyPI account and API token$(RESET)\n"
	@twine upload --repository testpypi dist/*
	@printf "$(GREEN)Published to Test PyPI!$(RESET)\n"
	@printf "Install with: pip install -i https://test.pypi.org/simple/ $(PACKAGE_NAME)==$(CURRENT_VERSION)\n"

.PHONY: publish
publish: check-publish build ## Publish to PyPI
	@printf "$(RED)Publishing to PyPI...$(RESET)\n"
	@printf "$(YELLOW)This will publish version $(CURRENT_VERSION) to the official PyPI$(RESET)\n"
	@read -p "Are you sure? (y/N) " -n 1 -r; \
	echo; \
	if [[ $$REPLY =~ ^[Yy]$$ ]]; then \
		printf "$(YELLOW)Publishing to PyPI...$(RESET)\n"; \
		twine upload dist/*; \
		printf "$(GREEN)Successfully published $(PACKAGE_NAME) $(CURRENT_VERSION) to PyPI!$(RESET)\n"; \
		printf "Install with: pip install $(PACKAGE_NAME)==$(CURRENT_VERSION)\n"; \
	else \
		printf "$(YELLOW)Publishing cancelled.$(RESET)\n"; \
	fi

.PHONY: release
release: ## Create a new release (runs tests, builds, and publishes)
	@printf "$(BLUE)Creating new release for $(PACKAGE_NAME) $(CURRENT_VERSION)...$(RESET)\n"
	@make test
	@make lint
	@make build
	@printf "$(GREEN)All checks passed! Ready to publish.$(RESET)\n"
	@make publish

# ========== MCP Specific Commands ==========

.PHONY: install-desktop
install-desktop: ## Install to Claude Desktop
	@printf "$(GREEN)Installing to Claude Desktop...$(RESET)\n"
	@python -m hanzo_mcp.cli install-desktop
	@printf "$(GREEN)Installation complete! Restart Claude Desktop.$(RESET)\n"

.PHONY: run-dev
run-dev: ## Run MCP development server
	@printf "$(GREEN)Starting MCP development server...$(RESET)\n"
	@hanzo-mcp-dev

.PHONY: test-tools
test-tools: ## Test MCP tools interactively
	@printf "$(GREEN)Starting interactive tool testing...$(RESET)\n"
	@python -m hanzo_mcp.test_tools

# ========== Documentation ==========

.PHONY: docs
docs: ## Build documentation
	@printf "$(GREEN)Building documentation...$(RESET)\n"
	@cd docs && make html
	@printf "$(GREEN)Documentation built! Open docs/_build/html/index.html$(RESET)\n"

.PHONY: docs-serve
docs-serve: docs ## Build and serve documentation
	@printf "$(GREEN)Serving documentation on http://localhost:8000...$(RESET)\n"
	@cd docs/_build/html && python -m http.server

# Default target
.DEFAULT_GOAL := help