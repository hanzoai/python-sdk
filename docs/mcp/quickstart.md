# MCP Quickstart

Get started with hanzo-mcp in under 5 minutes.

## Installation

```bash
# With pip
pip install hanzo-mcp[tools-all]

# With uv (recommended)
uv pip install hanzo-mcp[tools-all]
```

## Running the Server

### With Claude Code

```bash
# Run directly
uvx hanzo-mcp

# Or with Python
python -m hanzo_mcp
```

### With Claude Desktop

Install the configuration automatically:

```bash
hanzo-mcp --install
```

Or manually add to `~/Library/Application Support/Claude/claude_desktop_config.json`:

```json
{
  "mcpServers": {
    "hanzo": {
      "command": "uvx",
      "args": ["hanzo-mcp"]
    }
  }
}
```

Restart Claude Desktop after configuration.

## Basic Usage

Once running, you have access to 30+ tools:

### File Operations

```
Read a file: read("/path/to/file.py")
Write a file: write("/path/to/file.py", "content")
Edit a file: edit("/path/to/file.py", "old", "new")
```

### Command Execution

```
Run command: cmd("ls -la")
Run parallel: cmd(["npm install", "cargo build"], parallel=True)
```

### Search

```
Search files: search("pattern", path="./src")
Find files: find("*.py", path=".")
AST search: ast("def test_", path="./tests")
```

### Memory

```
Store memory: create_memories(["User prefers dark mode"])
Recall: recall_memories(["user preferences"])
```

## Transport Modes

### stdio (default)

Used by Claude Code and Claude Desktop:

```bash
hanzo-mcp --transport stdio
```

### SSE (Server-Sent Events)

For web clients and debugging:

```bash
hanzo-mcp --transport sse --port 8888
```

Access at `http://localhost:8888`

## Environment Variables

| Variable | Description |
|----------|-------------|
| `HANZO_AUTO_BACKGROUND_TIMEOUT` | Auto-background timeout (default: 30s, 0 to disable) |
| `HANZO_DEFAULT_SHELL` | Default shell (default: zsh) |
| `OPENAI_API_KEY` | For LLM tools |
| `ANTHROPIC_API_KEY` | For LLM tools |

## Next Steps

- [Configuration](configuration.md) - Detailed configuration options
- [Tools Reference](../tools/index.md) - All available tools
- [VS Code Setup](vscode.md) - IDE integration
