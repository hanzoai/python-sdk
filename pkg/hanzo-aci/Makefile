SHELL = /usr/bin/env bash

# Variables
PYTHON_VERSION      = 3.12
VENV_DIR            = .venv
PRE_COMMIT_CONFIG   = "./dev_config/python/.pre-commit-config.yaml"

# ANSI Color Codes
GREEN  := $(shell tput setaf 2)
YELLOW := $(shell tput setaf 3)
RED    := $(shell tput setaf 1)
BLUE   := $(shell tput setaf 6)
RESET  := $(shell tput sgr0)

# Setup: Install Python (if needed), create virtualenv, and install project in editable mode.
setup:
	@echo "$(YELLOW)Setting up environment...$(RESET)"
	@if ! command -v python$(PYTHON_VERSION) &>/dev/null; then \
	  echo "$(BLUE)Installing Python $(PYTHON_VERSION) with uv...$(RESET)"; \
	  uv python install $(PYTHON_VERSION); \
	fi
	@if [ ! -d "$(VENV_DIR)" ]; then \
	  echo "$(BLUE)Creating virtual environment...$(RESET)"; \
	  uv venv $(VENV_DIR) --python=$(PYTHON_VERSION); \
	fi
	@echo "$(BLUE)Installing project dependencies...$(RESET)"
	@. $(VENV_DIR)/bin/activate && uv pip install -e .
	@echo "$(GREEN)Setup complete.$(RESET)"

# Install pre-commit hooks
install-pre-commit-hooks:
	@echo "$(YELLOW)Installing pre-commit hooks...$(RESET)"
	@git config --unset-all core.hooksPath || true
	@. $(VENV_DIR)/bin/activate && uv pip install pre-commit && pre-commit install --config $(PRE_COMMIT_CONFIG)
	@echo "$(GREEN)Pre-commit hooks installed successfully.$(RESET)"

# Lint Python code using pre-commit hooks
lint-python:
	@echo "$(YELLOW)Running linters...$(RESET)"
	@. $(VENV_DIR)/bin/activate && pre-commit run --files dev_aci/**/* tests/**/* --show-diff-on-failure --config $(PRE_COMMIT_CONFIG)

lint: lint-python

# Build distribution packages using build (requires the 'build' package)
build:
	@echo "$(YELLOW)Building distribution packages...$(RESET)"
	@. $(VENV_DIR)/bin/activate && uv pip install build && python -m build
	@echo "$(GREEN)Build complete. Distributions available in ./dist.$(RESET)"

# Publish packages to PyPI using twine
publish: build
	@echo "$(YELLOW)Publishing packages to PyPI...$(RESET)"
	@. $(VENV_DIR)/bin/activate && uv pip install twine && python -m twine upload dist/*
	@echo "$(GREEN)Publish complete.$(RESET)"

# Clean build artifacts
clean:
	@echo "$(YELLOW)Cleaning build artifacts...$(RESET)"
	@rm -rf build dist *.egg-info
	@echo "$(GREEN)Clean complete.$(RESET)"
