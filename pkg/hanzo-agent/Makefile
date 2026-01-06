.PHONY: sync
sync:
	uv sync --all-extras --all-packages --group dev

.PHONY: format
format: 
	uv run ruff format

.PHONY: lint
lint: 
	uv run ruff check

.PHONY: mypy
mypy: 
	uv run mypy .

.PHONY: tests
tests: 
	uv run pytest 

.PHONY: old_version_tests
old_version_tests: 
	UV_PROJECT_ENVIRONMENT=.venv_39 uv run --python 3.9 -m pytest
	UV_PROJECT_ENVIRONMENT=.venv_39 uv run --python 3.9 -m mypy .

.PHONY: build-docs
build-docs:
	uv run mkdocs build

.PHONY: serve-docs
serve-docs:
	uv run mkdocs serve

.PHONY: deploy-docs
deploy-docs:
	uv run mkdocs gh-deploy --force --verbose

.PHONY: test-backend
test-backend:
	@echo "Testing Hanzo Agent SDK with local backend..."
	@echo "Make sure Router is running at http://localhost:4000"
	@echo "----------------------------------------"
	uv run python test_hanzo_backend.py

.PHONY: example-backend
example-backend:
	@echo "Running Hanzo backend integration example..."
	uv run python examples/hanzo_backend_example.py

.PHONY: setup-backend
setup-backend:
	@echo "Setting up Hanzo backend environment..."
	@echo "export HANZO_ROUTER_URL=http://localhost:4000/v1"
	@echo "export HANZO_API_KEY=sk-1234"
	@echo "----------------------------------------"
	@echo "Add these to your shell profile or .env file"
	
