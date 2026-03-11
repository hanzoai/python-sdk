# LLM.md - Hanzo Python SDK

## Quick Start

```bash
uv sync --all-packages
uv run python -c "from hanzoai import __version__; print(__version__)"
```

## Packages

### Core (Workspace Members)
| Package | Import | Description |
|---------|--------|-------------|
| hanzoai | `import hanzoai` | Official Hanzo API client |
| hanzo-mcp | `import hanzo_mcp` | MCP server with 39 tools |
| hanzo-memory | `import hanzo_memory` | Memory service with SQLite/vector |
| hanzo-repl | `import hanzo_repl` | Interactive REPL |
| hanzo-agent | `import hanzo_agent` | Agent framework |

### Tool Packages (Entry Points)
All tools discovered via `[project.entry-points."hanzo.tools"]`:

- `hanzo-tools-shell` - zsh, ps, open, npx, uvx
- `hanzo-tools-browser` - Playwright automation
- `hanzo-tools-fs` - read, write, edit, tree, find, search, ast
- `hanzo-tools-memory` - Unified memory tool
- `hanzo-tools-reasoning` - think, critic
- `hanzo-tools-agent` - CLI agent runner, iching, review
- `hanzo-tools-api` - Generic REST API via OpenAPI
- `hanzo-tools-lsp` - Language server protocol
- `hanzo-tools-refactor` - AST-based refactoring
- `hanzo-tools-llm` - LLM calls, consensus

## Architecture

```
hanzo-mcp (thin wrapper)
  └── discovers tools via entry points from hanzo-tools-* packages

hanzo-tools-*
  └── each exports TOOLS list via entry point
```

**Entry Point Pattern:**
```toml
[project.entry-points."hanzo.tools"]
shell = "hanzo_tools.shell:TOOLS"
```

## Key Patterns

### Tool Registration
```python
class MyTool(BaseTool):
    name = "my_tool"

    @property
    def description(self) -> str:
        return "Tool description"

    async def call(self, ctx, **params) -> str:
        pass
```

### Async (Non-blocking)
```python
# Use asyncio subprocess
proc = await asyncio.create_subprocess_exec(*cmd, stdout=PIPE, stderr=PIPE)
stdout, stderr = await asyncio.wait_for(proc.communicate(), timeout=30)

# Use aiofiles for file I/O
async with aiofiles.open(path) as f:
    content = await f.read()
```

### Auto-backgrounding
Commands auto-background after 45s. Use `ps` tool to monitor.

## Memory System

SQLite-based with optional vector search (sqlite-vec).

```
~/.hanzo/
├── memory/           # Global markdown files
└── db/
    └── global.db     # SQLite with FTS5

/project/.hanzo/
├── memory/           # Project memories
└── db/
    └── memory.db     # Project database
```

**Backends:** local (default), sqlite, lancedb (optional), kuzudb (optional)

## API Tool

Generic REST API tool with OpenAPI specs.

```python
api(action="list")                                    # List providers
api(action="config", provider="github", api_key="x") # Configure
api(action="call", provider="github", operation="listRepos")
```

Auto-detects: `GITHUB_TOKEN`, `CLOUDFLARE_API_TOKEN`, `OPENAI_API_KEY`, etc.

### Hanzo API Providers

All Hanzo services have unified OpenAPI specs at `/Users/z/work/hanzo/openapi/`:

| Provider | Service | Base URL | Spec |
|----------|---------|----------|------|
| `hanzo` | Unified API | api.hanzo.ai | `hanzo.yaml` |
| `hanzo-iam` | Identity/Auth | iam.hanzo.ai | `iam/openapi.yaml` |
| `hanzo-gateway` | LLM Gateway | gateway.hanzo.ai | `gateway/openapi.yaml` |
| `hanzo-commerce` | E-commerce | api.hanzo.ai/v1 | `commerce/openapi.yaml` |
| `hanzo-vector` | Vector DB | vector.hanzo.ai | `vector/openapi.yaml` |
| `hanzo-cloud` | AI Platform | cloud.hanzo.ai | `cloud/openapi.yaml` |
| `hanzo-nexus` | RAG/Knowledge | nexus.hanzo.ai | `nexus/openapi.yaml` |

```python
# Example: Call IAM API
api(action="spec", provider="hanzo-iam")
api(action="ops", provider="hanzo-iam", search="user")
api(action="call", provider="hanzo-iam", operation="getUser", params='{"id": "admin/user1"}')
```

## Testing

```bash
uv run pytest tests/ -v
uv run python -c "from hanzoai import __version__; print(__version__)"
```

## Common Issues

**Import error:** Run `uv sync --all-packages`

**Missing tool:** Check entry point in package's pyproject.toml

**Backend not available:** Install optional deps (lancedb, kuzu, sqlite-vec)
