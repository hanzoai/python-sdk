# Tools Overview

Complete documentation for all `hanzo-tools-*` packages.

> **Architecture**: Tools follow [HIP-0300](../hip/HIP-0300.md) - the Unified MCP Tools Architecture with orthogonal operators and effect tracking.

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

### HIP-0300 Core Operators

Primary operators organized by orthogonal axes:

| Tool | Axis | Actions | Description |
|------|------|---------|-------------|
| [fs](fs.md) | Bytes + Paths | read, write, edit, search, patch, tree | Filesystem operations |
| [id](core.md) | Identity | hash, uri, ref, verify | Content-addressable identity |
| [code](code.md) | Symbols + Structure | parse, transform, summarize | Code analysis and transformation |
| [proc](shell.md) | Execution | run, bg, signal, wait | Process execution |
| [vcs](vcs.md) | History + Diffs | status, diff, commit, log | Version control |
| [test](test.md) | Validation | check, build, test | Validation loops |
| [net](net.md) | Network | search, fetch, download, crawl | Network operations |
| [plan](plan.md) | Orchestration | intent, route, compose | Intent routing |

### Control Surfaces

| Tool | Surface | Description |
|------|---------|-------------|
| [browser](browser.md) | Web DOM | Playwright automation (70+ actions) |
| [computer](computer.md) | OS Desktop | Mac automation via pyautogui |

### Extended Operators

| Tool | Domain | Description |
|------|--------|-------------|
| [lsp](lsp.md) | Semantic Stream | Language server protocol (diagnostics, code_actions) |
| [memory](memory.md) | Knowledge | Persistent memory and knowledge bases |
| [todo](todo.md) | Task Tracking | Task management |
| [reasoning](reasoning.md) | Cognition | Structured thinking (think, critic) |
| [agent](agent.md) | Multi-Agent | Agent orchestration (run, list, status) |
| [llm](llm-tools.md) | LLM Interface | Unified LLM interface (llm, consensus) |

### Infrastructure

| Package | Tools | Description |
|---------|-------|-------------|
| [Core](core.md) | Base classes | BaseTool, IdTool, ToolRegistry |
| [Config](config.md) | 2 | Configuration and mode management |
| [Database](database.md) | 8 | SQL and graph database operations |
| [Vector](vector.md) | 3 | Semantic search with embeddings |
| [Refactor](refactor.md) | 1 | Code refactoring (rename, extract, inline) |
| [Jupyter](jupyter.md) | 1 | Notebook read/edit/execute |
| [Editor](editor.md) | 3 | Neovim integration |
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
