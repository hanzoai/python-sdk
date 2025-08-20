# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Repository Overview

This is the Hanzo Python SDK monorepo containing the official Python client library for the Hanzo AI platform and related packages. The SDK provides unified access to 100+ LLM providers through a single OpenAI-compatible API interface, with enterprise features like cost tracking, rate limiting, and observability.

## Project Structure

This is a monorepo managed with `rye` containing multiple interconnected packages:

### Main Package
- **`pkg/hanzoai/`** - Core SDK for Hanzo AI platform
  - OpenAI-compatible API client
  - Support for 100+ LLM providers
  - Cost tracking and rate limiting
  - Team and organization management
  - File operations and fine-tuning

### Sub-Packages (in `pkg/` directory)
- **`hanzo/`** - CLI and orchestration tools
- **`hanzo-mcp/`** - Model Context Protocol implementation
- **`hanzo-agents/`** - Agent framework and swarm orchestration
- **`hanzo-memory/`** - Memory and knowledge base management
- **`hanzo-network/`** - Distributed network capabilities
- **`hanzo-repl/`** - Interactive REPL for AI chat
- **`hanzo-aci/`** - AI code intelligence and editing tools

## Development Commands

### Setup and Installation
```bash
# Install Python via uv (required)
make install-python

# Complete setup (venv + dependencies)
make setup

# Install specific package for development
uv pip install -e .
uv pip install -e ./pkg/hanzo-agents
```

### Testing
```bash
# Run all tests
make test
./scripts/test

# Run specific test file
uv run pytest tests/api_resources/test_chat.py -v

# Run tests with specific pattern
uv run pytest -k "pattern" -v

# Run tests with coverage
uv run pytest --cov=hanzoai tests/

# Run tests for specific package
make test-agents  # Test hanzo-agents
make test-mcp     # Test hanzo-mcp
```

### Code Quality
```bash
# Format code
make format
ruff format pkg/

# Run linting
make lint
ruff check . --fix

# Type checking
make check-types
uv run mypy pkg/hanzoai --ignore-missing-imports
uv run pyright
```

### Building and Publishing
```bash
# Build all packages
make build

# Build specific package
uv build .
cd pkg/hanzo-mcp && uv build

# Check packages before publishing
make publish-check
```

## Architecture and Code Organization

### Client Architecture
The SDK uses a code-generated client architecture (via Stainless):
- **Base Client** (`_base_client.py`) - HTTP client with retry logic
- **Main Client** (`_client.py`) - `Hanzo` and `AsyncHanzo` classes
- **Resources** (`resources/`) - API endpoint implementations
  - Each resource follows a consistent pattern with sync/async support
  - Resources are organized by API domain (chat, files, models, etc.)
- **Types** (`types/`) - Pydantic models for request/response types

### Key Patterns

#### Resource Pattern
All API resources follow this structure:
```python
class ResourceWithRawResponse:
    def __init__(self, resource: Resource) -> None:
        self._resource = resource
        # Expose methods with raw response wrapper

class AsyncResourceWithRawResponse:
    # Async version of the above
```

#### Testing Pattern
Tests use `respx` for HTTP mocking (no external dependencies):
```python
@pytest.mark.respx(base_url=base_url)
def test_method(client: Hanzo, respx_mock: MockRouter) -> None:
    respx_mock.get("/endpoint").mock(return_value=Response(200, json={}))
    # Test implementation
```

### Important Implementation Details

1. **Environment Variables**:
   - `HANZO_API_KEY` - API authentication
   - `HANZO_BASE_URL` - API base URL (default: https://api.hanzo.ai)
   - `HANZO_LOG` - Logging level (debug/info/warning/error)

2. **Dependency Management**:
   - Uses `rye` for workspace management
   - `uv` for fast Python package operations
   - Separate lock files for production and dev dependencies

3. **Test Infrastructure**:
   - All tests use mocked responses (no external API calls)
   - 100% test coverage requirement
   - Tests organized by resource in `tests/api_resources/`

4. **Code Generation**:
   - Many files are auto-generated from OpenAPI spec
   - Look for "File generated from our OpenAPI spec" header
   - Manual changes to generated files will be overwritten

## Package-Specific Notes

### hanzo-mcp
- Implements Model Context Protocol for tool capabilities
- Includes filesystem, search, and agent delegation tools
- Can be installed to Claude Desktop with `make install-desktop`

### hanzo-agents
- Provides agent swarm orchestration
- Supports both hierarchical and peer network architectures
- Includes MCP tool integration for recursive agent calls

### hanzo CLI
- Main entry point: `hanzo.cli:main`
- Subcommands for auth, chat, mcp, network operations
- Supports local AI orchestration with `hanzo dev`

## Common Tasks

### Adding New API Endpoints
1. Update OpenAPI spec if using code generation
2. Add resource class in `resources/` directory
3. Add types in `types/` directory
4. Add tests in `tests/api_resources/`
5. Update `__init__.py` exports

### Running Local Development Server
```bash
# Start mock server for testing
python run_mock_server.py

# Run hanzo dev with local orchestration
hanzo dev --orchestrator local:llama-3.2-3b
```

### Debugging Tests
```bash
# Run with verbose output
uv run pytest -vv tests/

# Run with print statements visible
uv run pytest -s tests/

# Run specific test with debugging
uv run pytest tests/test_client.py::TestClient::test_method -vv
```

## CI/CD Pipeline

The repository uses GitHub Actions for CI:
- **Linting** - Runs on every push/PR with `ruff`
- **Testing** - Full test suite with coverage reporting
- **Type Checking** - Both `mypy` and `pyright`
- **Package Testing** - Separate CI for each sub-package

## Important Conventions

1. **No Print Statements**: Use logging instead, except in CLI tools
2. **Type Hints Required**: All functions must have type annotations
3. **Async Support**: All API methods have both sync and async versions
4. **Error Handling**: Use specific exception classes from `_exceptions.py`
5. **Documentation**: Docstrings for public APIs, examples in `/examples`