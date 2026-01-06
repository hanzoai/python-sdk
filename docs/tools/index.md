# Tools Overview

Complete documentation for all `hanzo-tools-*` packages.

## Installation

```bash
# All tools (recommended)
pip install hanzo-mcp[tools-all]

# Core development tools
pip install hanzo-mcp[tools-dev]

# Individual packages
pip install hanzo-tools-shell hanzo-tools-browser
```

## Tool Categories

### Core Infrastructure

| Package | Tools | Description |
|---------|-------|-------------|
| [Core](core.md) | Base classes | Foundation for tool development |
| [Config](config.md) | 2 | Configuration and mode management |

### File & Code Operations

| Package | Tools | Description |
|---------|-------|-------------|
| [Filesystem](fs.md) | 7 | read, write, edit, tree, find, search, ast |
| [LSP](lsp.md) | 1 | Language server protocol (definition, references, hover) |
| [Refactor](refactor.md) | 1 | Code refactoring (rename, extract, inline) |

### Shell & Execution

| Package | Tools | Description |
|---------|-------|-------------|
| [Shell](shell.md) | 12 | cmd, ps, zsh, bash, fish, dash, npx, uvx, open, curl, jq, wget |
| [Computer](computer.md) | 1 | Mac automation via pyautogui |

### AI & Agents

| Package | Tools | Description |
|---------|-------|-------------|
| [Agent](agent.md) | 3 | Multi-agent orchestration (agent, iching, review) |
| [LLM](llm-tools.md) | 2 | Unified LLM interface (llm, consensus) |
| [Reasoning](reasoning.md) | 2 | Structured thinking (think, critic) |

### Data & Memory

| Package | Tools | Description |
|---------|-------|-------------|
| [Memory](memory.md) | 9 | Persistent memory and knowledge bases |
| [Database](database.md) | 8 | SQL and graph database operations |
| [Vector](vector.md) | 3 | Semantic search with embeddings |

### Specialized

| Package | Tools | Description |
|---------|-------|-------------|
| [Browser](browser.md) | 1 | Playwright automation (70+ actions) |
| [Jupyter](jupyter.md) | 1 | Notebook read/edit/execute |
| [Editor](editor.md) | 3 | Neovim integration |
| [Todo](todo.md) | 1 | Task management |
| [MCP](mcp-tools.md) | 4 | MCP server management |

## Quick Reference

### Most Used Tools

```python
# File operations
read(file_path="/path/to/file")
write(file_path="/path/to/file", content="...")
edit(file_path="/path/to/file", old_string="old", new_string="new")

# Command execution
cmd("ls -la")
cmd(["npm install", "npm build"], parallel=True)

# Search
search(pattern="TODO", path=".")
ast(pattern="def test_", path="/tests")

# Reasoning
think(thought="Analyzing the problem...")
critic(analysis="Code review findings...")

# Browser
browser(action="navigate", url="https://example.com")
browser(action="click", selector="button")
```

### Tool Discovery

```python
from importlib.metadata import entry_points

# Discover all available tools
for ep in entry_points(group="hanzo.tools"):
    tools = ep.load()
    print(f"{ep.name}: {[t.name for t in tools]}")
```

## Architecture

All tools follow a consistent pattern:

```python
from hanzo_tools.core import BaseTool, ToolContext

class MyTool(BaseTool):
    name = "my_tool"
    
    @property
    def description(self) -> str:
        return "Tool description"
    
    async def call(self, ctx: ToolContext, **params) -> str:
        # Implementation
        return result
```

## See Also

- [Core Libraries](../lib/index.md) - Supporting packages (async, consensus, network)
- [MCP Reference](../ref/mcp/index.md) - Server documentation
- [Agent Framework](../ref/agent/index.md) - Multi-agent SDK
