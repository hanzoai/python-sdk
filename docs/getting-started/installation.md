# Installation

## Requirements

- Python 3.12 or higher
- pip, uv, or pipx for package management

## Quick Install

### Using pip

```bash
# Full install with all tools
pip install hanzo-mcp[tools-all]

# Or just the MCP server
pip install hanzo-mcp

# Or just the agent SDK
pip install hanzo-agent
```

### Using uv (Recommended)

[uv](https://github.com/astral-sh/uv) is the fastest Python package manager:

```bash
# Install uv first
curl -LsSf https://astral.sh/uv/install.sh | sh

# Install hanzo-mcp
uv pip install hanzo-mcp

# Run directly without installing
uvx hanzo-mcp
```

### Using pipx (Isolated)

```bash
pipx install hanzo-mcp
```

## Optional Dependencies

Install specific tool packages as needed:

```bash
# Browser automation (Playwright)
pip install hanzo-tools-browser

# Database tools
pip install hanzo-tools-database

# Vector search
pip install hanzo-tools-vector[full]
```

## Bundles

Choose a bundle based on your needs:

| Bundle | Packages | Use Case |
|--------|----------|----------|
| `hanzo-mcp` | Core MCP only | Minimal install |
| `hanzo-mcp[tools-core]` | fs, shell, memory, reasoning | Essential tools |
| `hanzo-mcp[tools-dev]` | + lsp, refactor, browser | Development |
| `hanzo-mcp[tools-all]` | All 30+ tools | Full features |

## VS Code Extension

For VS Code, Cursor, or Antigravity:

1. Install the Hanzo extension from the marketplace
2. The extension auto-detects `uvx` and uses Python MCP by default
3. Configure the backend in settings:

```json
{
  "hanzo.mcp.backend": "auto",
  "hanzo.mcp.pythonCommand": "uvx hanzo-mcp"
}
```

## Verify Installation

```bash
# Check version
uvx hanzo-mcp --version

# Run in stdio mode (for MCP clients)
uvx hanzo-mcp --transport stdio

# Run development server
uvx hanzo-mcp-dev
```

## Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `HANZO_AUTO_BACKGROUND_TIMEOUT` | Auto-background timeout (seconds, 0 to disable) | `45` |
| `HANZO_MCP_TRANSPORT` | Transport mode (stdio, tcp) | `stdio` |
| `HANZO_MCP_PORT` | TCP port when using tcp transport | `3000` |
| `HANZO_ALLOWED_PATHS` | Comma-separated allowed paths | (none) |

## Troubleshooting

### uvx not found

```bash
# Install uv first
curl -LsSf https://astral.sh/uv/install.sh | sh

# Reload shell
source ~/.bashrc  # or ~/.zshrc
```

### Permission errors

```bash
# Use user install
pip install --user hanzo-mcp

# Or use a virtual environment
python -m venv .venv
source .venv/bin/activate
pip install hanzo-mcp
```

### Python version

Ensure Python 3.12+:

```bash
python --version
# Python 3.12.x

# If needed, install with pyenv
pyenv install 3.12
pyenv global 3.12
```
