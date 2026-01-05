# Hanzo MCP

Hanzo MCP is a comprehensive Model Context Protocol server that provides 30+ tools for AI code assistants like Claude Code, Cursor, and VS Code Copilot.

## What is MCP?

The Model Context Protocol (MCP) is a standard for connecting AI assistants to external tools and data sources. Hanzo MCP implements this protocol with a focus on:

- **Developer Tools** - File operations, shell commands, code search
- **Browser Automation** - Full Playwright integration with 70+ actions
- **AI Reasoning** - Structured thinking and critical analysis tools
- **Memory** - Persistent knowledge storage and retrieval
- **Multi-Agent** - Spawn and coordinate external AI agents

## Architecture

```
┌─────────────────────────────────────────────────────────┐
│                    AI Assistant                          │
│              (Claude, Cursor, VS Code)                   │
└─────────────────┬───────────────────────────────────────┘
                  │ MCP Protocol (stdio/tcp)
                  ▼
┌─────────────────────────────────────────────────────────┐
│                   hanzo-mcp                              │
│  ┌─────────────┐ ┌─────────────┐ ┌─────────────┐       │
│  │ hanzo-tools │ │ hanzo-tools │ │ hanzo-tools │  ...  │
│  │   -shell    │ │    -fs      │ │  -browser   │       │
│  └─────────────┘ └─────────────┘ └─────────────┘       │
└─────────────────────────────────────────────────────────┘
```

## Tool Categories

### File System (`hanzo-tools-fs`)
- `read` - Read file contents with line numbers
- `write` - Write content to files
- `edit` - Find and replace in files
- `tree` - Display directory structure
- `find` - Find files by pattern
- `search` - Search file contents (regex)
- `ast` - AST-based code search

### Shell (`hanzo-tools-shell`)
- `cmd` - Unified command execution with DAG support
- `zsh`, `bash` - Shell-specific execution
- `ps` - Process management (list, kill, logs)
- `npx`, `uvx` - Package runner shortcuts
- `open` - Open files/URLs in default app

### Browser (`hanzo-tools-browser`)
- 70+ Playwright actions
- Navigation, forms, mouse, touch
- Device emulation (mobile, tablet, laptop)
- Assertions and waits
- Network interception
- Multi-context for parallel agents

### Memory (`hanzo-tools-memory`)
- `memory` - Unified memory operations
  - `recall` - Search memories
  - `create` - Store new memories
  - `update` - Modify memories
  - `delete` - Remove memories
  - `facts` - Knowledge base queries
  - `summarize` - Create memory summaries

### Reasoning (`hanzo-tools-reasoning`)
- `think` - Structured reasoning tool
- `critic` - Critical analysis and review

### LSP & Refactor (`hanzo-tools-lsp`, `hanzo-tools-refactor`)
- Go-to-definition
- Find references
- Rename symbols
- Extract functions/variables
- Change signatures

### Agent (`hanzo-tools-agent`)
- `agent` - Run external AI agents
  - Claude, Gemini, Codex, Grok, Qwen
- `iching` - Engineering wisdom oracle
- `review` - Code review requests

### LLM (`hanzo-tools-llm`)
- `llm` - Direct LLM access
- `consensus` - Multi-model consensus

## Key Features

### Auto-Backgrounding

Long-running commands automatically background after 45 seconds:

```python
cmd("npm install")  # Auto-backgrounds if slow

# Check background processes
ps()                    # List all
ps(logs="cmd_xxx")      # View output
ps(kill="cmd_xxx")      # Stop process
```

### DAG Execution

Execute complex workflows:

```python
cmd([
    "mkdir dist",
    {"parallel": ["cp a dist/", "cp b dist/"]},
    "zip -r out.zip dist/"
])
```

### Multiple Backends

The VS Code extension supports multiple MCP backends:

| Backend | Command | Features |
|---------|---------|----------|
| Python (default) | `uvx hanzo-mcp` | Full 30+ tools |
| TypeScript | Built-in | Essential tools |
| Rust | `hanzo-mcp` binary | High performance |
| Local Node | hanzod | Network deployment |

## Getting Started

1. [Installation](../getting-started/installation.md)
2. [Quickstart](quickstart.md)
3. [Configuration](configuration.md)
4. [VS Code Extension](vscode.md)
