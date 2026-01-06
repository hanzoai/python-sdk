# MCP Implementation Parity Analysis

This document analyzes the parity status between Hanzo's three MCP implementations and provides a roadmap for convergence.

## Architecture Overview

```
┌─────────────────────────────────────────────────────────────────┐
│                        VS Code Extension                         │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │                    Backend Selection                       │   │
│  │  auto → python (if uvx) → typescript (fallback)          │   │
│  └──────────────────────────────────────────────────────────┘   │
└───────────┬──────────────────┬────────────────────┬─────────────┘
            │                  │                    │
            ▼                  ▼                    ▼
┌───────────────────┐ ┌────────────────┐ ┌──────────────────────┐
│  Python MCP       │ │ TypeScript MCP │ │   Rust MCP Client    │
│  (hanzo-mcp)      │ │ (@hanzo/mcp)   │ │   (hanzo-node)       │
│                   │ │                │ │                      │
│  30+ native tools │ │ 15+ tools      │ │  MCP proxy/client    │
│  Full features    │ │ Essential set  │ │  Connects to others  │
└───────────────────┘ └────────────────┘ └──────────────────────┘
```

## Implementation Comparison

### Python MCP (`hanzo-mcp`) - Reference Implementation

**Status: Complete (30+ tools)**

| Category | Tools | Status |
|----------|-------|--------|
| **File System** | read, write, edit, tree, find, search, ast | ✅ Complete |
| **Shell** | cmd, zsh, bash, ps, npx, uvx, open | ✅ Complete |
| **Browser** | 70+ Playwright actions | ✅ Complete |
| **Memory** | unified memory (recall, create, update, delete, facts) | ✅ Complete |
| **Reasoning** | think, critic | ✅ Complete |
| **LSP** | definition, references, rename, hover | ✅ Complete |
| **Refactor** | rename, extract, inline, move | ✅ Complete |
| **Agent** | agent runner (claude, gemini, codex, etc.), iching, review | ✅ Complete |
| **LLM** | llm, consensus | ✅ Complete |
| **Todo** | unified todo management | ✅ Complete |
| **Config** | config, mode | ✅ Complete |
| **Database** | SQL query/search/stats, graph operations | ✅ Complete |
| **Vector** | index, vector_index, vector_search | ✅ Complete |
| **Jupyter** | notebook read/edit | ✅ Complete |
| **Editor** | neovim integration | ✅ Complete |

**Key Features:**
- ✅ Auto-backgrounding (45s default, configurable via `HANZO_AUTO_BACKGROUND_TIMEOUT`)
- ✅ DAG execution with parallel support
- ✅ Process management (ps tool)
- ✅ Entry-point based tool discovery
- ✅ Unified action patterns (memory, agent tools)
- ✅ 701 programmer personas

### TypeScript MCP (`@hanzo/mcp`) - Essential Subset

**Status: Partial (~15 tools)**

| Category | Tools | Status |
|----------|-------|--------|
| **File System** | read_file, write_file, list_files, get_file_info, directory_tree | ✅ Complete |
| **Shell** | bash, run_command, run_background, list_processes, get_process_output, kill_process | ✅ Complete |
| **Search** | grep, search | ✅ Complete |
| **Edit** | edit tools | ✅ Complete |
| **Browser** | HanzoDesktopTool, PlaywrightControlTool | ⚠️ Basic |
| **Memory** | separate memory tools | ⚠️ Not unified |
| **Reasoning** | - | ❌ Missing |
| **UI** | unified-ui, ui-registry, github-ui | ✅ Complete |
| **AutoGUI** | automation tools | ✅ Complete |
| **Orchestration** | agent tools | ⚠️ Basic |

**Features Comparison:**
| Feature | Python | TypeScript | Gap |
|---------|--------|------------|-----|
| Auto-backgrounding | ✅ 45s | ✅ `withAutoTimeout` | Parity |
| DAG execution | ✅ `cmd` tool | ❌ | **Missing** |
| Process management | ✅ Unified `ps` | ⚠️ Separate tools | Different API |
| Unified memory | ✅ Single tool | ❌ | **Missing** |
| Think/Critic | ✅ | ❌ | **Missing** |
| Personas | ✅ 701 | ❌ | **Missing** |

### Rust MCP (`hanzo-node/hanzo-mcp`) - MCP Client/Proxy

**Status: Different Architecture**

The Rust implementation is an **MCP client**, not a tool provider. It:

1. Connects to external MCP servers (via stdio, SSE, HTTP)
2. Lists tools from connected servers
3. Proxies tool calls to those servers

**Supported Transports:**
- ✅ Stdio (spawns MCP server as subprocess)
- ✅ SSE (Server-Sent Events)
- ✅ HTTP (Streamable HTTP)

**Use Case:**
- Embedded in `hanzo-node` (blockchain/AI node)
- Orchestrates multiple MCP servers
- Enables decentralized tool execution

## Parity Roadmap

### Phase 1: TypeScript Essential Parity (Priority: P0)

Add missing essential tools to TypeScript MCP:

1. **`cmd` tool with DAG support**
   ```typescript
   cmd({ commands: ["npm install", "npm build"], parallel: true })
   cmd({ commands: [
     { id: "install", run: "npm install" },
     { id: "build", run: "npm build", after: ["install"] }
   ]})
   ```

2. **Unified `ps` tool**
   - Consolidate list_processes, get_process_output, kill_process
   - Match Python API: `ps()`, `ps({ logs: "id" })`, `ps({ kill: "id" })`

3. **`think` and `critic` tools**
   - Essential for AI reasoning patterns
   - Simple implementation, high value

### Phase 2: TypeScript Feature Parity (Priority: P1)

1. **Unified `memory` tool**
   - Match Python's action-based API
   - Actions: recall, create, update, delete, facts, summarize

2. **Enhanced browser tool**
   - Add more Playwright actions
   - Match Python's 70+ action coverage

3. **Agent tool**
   - Unified interface for spawning external agents
   - Support for Claude, Gemini, Codex, etc.

### Phase 3: Rust Tool Implementation (Priority: P2)

Consider adding native Rust tools for performance-critical operations:

1. **File I/O** - High-performance read/write/search
2. **Process management** - Native subprocess handling
3. **AST parsing** - Tree-sitter based code analysis

This would allow `hanzo-node` to run standalone without Python dependency.

## Extension Backend Selection Logic

The VS Code extension (`~/work/hanzo/extension`) uses this selection:

```typescript
async selectBackend(backend: string): Promise<string> {
  if (backend !== 'auto') return backend;

  // Auto-detect: prefer Python if uvx available
  try {
    execSync('uvx --version', { stdio: 'ignore' });
    return 'python';  // Full 30+ tools
  } catch {
    return 'typescript';  // Essential ~15 tools
  }
}
```

**Backend Capabilities:**

| Backend | Tools | Use Case |
|---------|-------|----------|
| `python` | 30+ | Full development (recommended) |
| `typescript` | ~15 | Web-first, no Python needed |
| `rust` | (proxy) | High-performance, embedded |
| `local-node` | varies | Decentralized compute |

## Tool Name Mapping

For swappable backends, tool names should be consistent:

| Python | TypeScript | Rust | Action |
|--------|------------|------|--------|
| `read` | `read_file` | - | **Align to `read`** |
| `write` | `write_file` | - | **Align to `write`** |
| `cmd` | `bash` | - | **Add `cmd` to TS** |
| `ps` | `list_processes` | - | **Add unified `ps`** |
| `tree` | `directory_tree` | - | **Align to `tree`** |
| `search` | `grep` | - | Keep both as aliases |

## Recommended Actions

### Immediate (This Sprint)

1. ✅ Extension supports multiple backends (done)
2. ✅ Python MCP is reference (done)
3. ⬜ Document tool name differences
4. ⬜ Create TypeScript `cmd` tool issue

### Short Term (Next 2 Sprints)

1. ⬜ Add `cmd` with DAG to TypeScript
2. ⬜ Add `think`/`critic` to TypeScript
3. ⬜ Unify `ps` in TypeScript
4. ⬜ Align tool names (read vs read_file)

### Medium Term

1. ⬜ Unified `memory` in TypeScript
2. ⬜ Enhanced browser tool
3. ⬜ Consider Rust native tools

## Testing Parity

To ensure backends are swappable, run same tests against all:

```bash
# Python
uvx hanzo-mcp --test

# TypeScript
npx @hanzo/mcp --test

# Via extension (auto-detect)
code --command "hanzo.mcp.test"
```

## Conclusion

The current architecture is sound:
- **Python**: Reference implementation with full features
- **TypeScript**: Essential subset for browser/VS Code
- **Rust**: Client/proxy for orchestration

The priority is bringing TypeScript to essential parity (cmd, ps, think, critic), not full parity. Users needing all features should use Python backend.
