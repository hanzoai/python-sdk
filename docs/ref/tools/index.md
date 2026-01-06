# Tools Reference

Comprehensive API reference for all hanzo-tools-* packages.

## Tool Packages

| Package | Tools | Description |
|---------|-------|-------------|
| [Core](../../tools/core.md) | Base classes | Foundation for tool development |
| [Filesystem](../../tools/fs.md) | 7 | File operations and AST analysis |
| [Shell](../../tools/shell.md) | 12 | Command execution and process management |
| [Browser](../../tools/browser.md) | 1 (70+ actions) | Playwright automation |
| [Memory](../../tools/memory.md) | 9 | Persistent memory and knowledge bases |
| [Reasoning](../../tools/reasoning.md) | 2 | Structured thinking and analysis |
| [Agent](../../tools/agent.md) | 3 | Multi-agent orchestration |
| [LSP](../../tools/lsp.md) | 1 | Language server protocol |
| [Refactor](../../tools/refactor.md) | 1 | Code refactoring with AST/LSP |
| [LLM](../../tools/llm-tools.md) | 2 | Unified LLM interface |
| [Database](../../tools/database.md) | 8 | SQL and graph databases |
| [Vector](../../tools/vector.md) | 3 | Semantic search |
| [Jupyter](../../tools/jupyter.md) | 1 | Notebook operations |
| [Editor](../../tools/editor.md) | 3 | Neovim integration |
| [Todo](../../tools/todo.md) | 1 | Task management |
| [Computer](../../tools/computer.md) | 1 | Mac automation |
| [Config](../../tools/config.md) | 2 | Configuration management |
| [MCP](../../tools/mcp-tools.md) | 4 | MCP server management |

## Quick Install

```bash
# All tools
pip install hanzo-mcp[tools-all]

# Core + dev tools
pip install hanzo-mcp[tools-dev]

# Specific packages
pip install hanzo-tools-shell hanzo-tools-browser
```

## Tool Discovery

Tools are discovered via entry points:

```python
from importlib.metadata import entry_points

# Get all tool entry points
eps = entry_points(group="hanzo.tools")
for name, ep in eps.items():
    tools = ep.load()
    print(f"{name}: {len(tools)} tools")
```

## See Also

- [MCP Configuration](../../mcp/configuration.md)
- [MCP Quickstart](../../mcp/quickstart.md)
