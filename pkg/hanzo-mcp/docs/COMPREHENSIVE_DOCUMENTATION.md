# 🥷 Hanzo MCP - Comprehensive Documentation

## Table of Contents

1. [Introduction](#introduction)
2. [Installation Guide](#installation-guide)
3. [Configuration Options](#configuration-options)
4. [API Reference](#api-reference)
5. [Example Use Cases](#example-use-cases)
6. [Troubleshooting Guide](#troubleshooting-guide)
7. [Architecture Overview](#architecture-overview)
8. [Advanced Topics](#advanced-topics)

---

## Introduction

Hanzo MCP (Model Context Protocol) is a comprehensive ecosystem of interconnected development tools designed for the AI era. It provides a unified interface to orchestrate your entire development workflow through the Model Context Protocol standard.

### Key Features

- **70+ Integrated Tools**: From file operations to AI orchestration
- **Multi-Language Support**: Python, JavaScript, Go, R, and more
- **Interactive Development**: Notebooks, REPL, and debugging
- **AI-Native**: Built-in agent systems and LLM integration
- **Extensible**: Add any MCP server or custom tool
- **Quality Focused**: Automated review, testing, and best practices

### Why Hanzo MCP?

Traditional development environments suffer from:
- Fragmented tools that don't communicate
- Context switching between interfaces
- No unified workflow orchestration
- Missing tool composition capabilities

Hanzo MCP solves these problems by providing:
- **Unified Ecosystem**: All tools work together seamlessly
- **Intelligent Orchestration**: Context-aware tool collaboration
- **Interactive Development**: From REPL to debugging in one interface
- **Built-in Quality**: Automated review and testing
- **Extensible Platform**: Add any MCP server or custom tool

---

## Installation Guide

### Prerequisites

- Python 3.12 or higher
- Git
- Node.js (optional, for npx support)

### Quick Installation

#### Method 1: Using uvx (Recommended)

```bash
# Install and run Hanzo MCP with one command
uvx hanzo-mcp

# Note: If uvx is not installed, Hanzo will automatically install it for you
```

#### Method 2: Using pip

```bash
# Install globally
pip install hanzo-mcp

# Or install in a virtual environment
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
pip install hanzo-mcp
```

#### Method 3: From Source

```bash
# Clone the repository
git clone https://github.com/hanzoai/mcp.git
cd mcp

# Install in development mode
pip install -e .

# Or use uv for development
uv pip install -e .
```

#### Method 4: Desktop Extension (One-Click)

1. Download the latest `.dxt` file from [releases](https://github.com/hanzoai/mcp/releases)
2. Double-click to install
3. The extension will be available in your desktop environment

### Post-Installation Setup

1. **Initialize Configuration**:
```bash
hanzo-mcp --init
```

2. **Verify Installation**:
```bash
hanzo-mcp --version
hanzo-mcp --health
```

3. **Configure Claude Desktop** (if using):
```bash
# Add to Claude Desktop's config
hanzo-mcp --claude-config
```

### Installation Options

```bash
# Install with specific features
pip install hanzo-mcp[agents]     # Agent support
pip install hanzo-mcp[memory]     # Memory system
pip install hanzo-mcp[analytics]  # Analytics tracking
pip install hanzo-mcp[dev]        # Development tools
pip install hanzo-mcp[all]        # Everything
```

---

## Configuration Options

### Configuration File Locations

Hanzo MCP looks for configuration in the following order (highest priority first):

1. CLI arguments
2. Environment variables
3. Project-specific config (`.hanzo/mcp-settings.json`)
4. Global config (`~/.config/hanzo/mcp-settings.json`)
5. Default settings

### Global Configuration

Create or edit `~/.config/hanzo/mcp-settings.json`:

```json
{
  "server": {
    "name": "hanzo-mcp",
    "host": "127.0.0.1",
    "port": 8888,
    "transport": "stdio",
    "log_level": "INFO",
    "command_timeout": 120.0
  },
  
  "allowed_paths": [
    "~/projects",
    "~/work",
    "/tmp"
  ],
  
  "enabled_tools": {
    "read": true,
    "write": true,
    "edit": true,
    "search": true,
    "agent": true,
    "critic": true
  },
  
  "disabled_tools": [
    "dangerous_tool"
  ],
  
  "agent": {
    "enabled": true,
    "model": "gpt-4",
    "api_key": "your-api-key-here",
    "max_iterations": 10,
    "max_tool_uses": 30
  },
  
  "vector_store": {
    "enabled": true,
    "provider": "infinity",
    "embedding_model": "text-embedding-3-small",
    "chunk_size": 1000,
    "chunk_overlap": 200
  },
  
  "mcp_servers": {
    "github": {
      "name": "github",
      "command": "npx",
      "args": ["@modelcontextprotocol/server-github"],
      "enabled": true,
      "trusted": true,
      "description": "GitHub integration"
    }
  }
}
```

### Environment Variables

All configuration options can be set via environment variables:

```bash
# Server configuration
export HANZO_MCP_HOST="127.0.0.1"
export HANZO_MCP_PORT="8888"
export HANZO_MCP_LOG_LEVEL="DEBUG"

# API Keys
export OPENAI_API_KEY="sk-..."
export ANTHROPIC_API_KEY="sk-ant-..."
export HANZO_API_KEY="hanzo-..."

# Paths
export HANZO_MCP_PROJECT_DIR="/path/to/project"
export HANZO_MCP_ALLOWED_PATHS="/home/user/projects,/tmp"

# Tool configuration
export HANZO_MCP_DISABLED_TOOLS="dangerous_tool,another_tool"
export HANZO_MCP_AGENT_MODEL="gpt-4"
```

### Project-Specific Configuration

Create `.hanzo/mcp-settings.json` in your project root:

```json
{
  "project": {
    "name": "my-project",
    "root_path": ".",
    "rules": [
      ".cursorrules",
      ".claude/code.md"
    ],
    "enabled_tools": {
      "agent": true,
      "critic": true
    },
    "disabled_tools": ["rm", "dangerous_operation"],
    "mcp_servers": ["github", "linear"]
  }
}
```

### CLI Configuration

```bash
# Set configuration via CLI
hanzo-mcp config set agent.model "gpt-4"
hanzo-mcp config set server.port 9999
hanzo-mcp config add allowed_paths "/new/path"

# View configuration
hanzo-mcp config show
hanzo-mcp config get agent.model

# Reset configuration
hanzo-mcp config reset
```

---

## API Reference

### Core Tools

#### File Operations

##### read
Read file contents with intelligent detection.

```python
read(file_path: str, limit: int = None, offset: int = None)
```

**Parameters:**
- `file_path` (str): Path to file to read
- `limit` (int, optional): Maximum lines to read
- `offset` (int, optional): Starting line number

**Returns:**
- File contents with line numbers

##### write
Write or create files.

```python
write(file_path: str, content: str)
```

**Parameters:**
- `file_path` (str): Path to file
- `content` (str): Content to write

##### edit
Edit files with precise replacements.

```python
edit(file_path: str, old_string: str, new_string: str, expected_replacements: int = 1)
```

**Parameters:**
- `file_path` (str): Path to file
- `old_string` (str): Text to replace
- `new_string` (str): Replacement text
- `expected_replacements` (int): Expected number of replacements

##### multi_edit
Make multiple edits in one operation.

```python
multi_edit(file_path: str, edits: List[Dict])
```

**Parameters:**
- `file_path` (str): Path to file
- `edits` (List[Dict]): List of edit operations

#### Search Tools

##### search (Unified Search)
Multi-modal search combining text, AST, vector, and symbol search.

```python
search(
    pattern: str,
    path: str = ".",
    enable_grep: bool = True,
    enable_ast: bool = True,
    enable_vector: bool = True,
    enable_symbol: bool = True,
    max_results: int = 50
)
```

**Parameters:**
- `pattern` (str): Search pattern or query
- `path` (str): Directory to search
- `enable_*` (bool): Enable specific search types
- `max_results` (int): Maximum results per search type

##### grep
Fast pattern matching with ripgrep.

```python
grep(
    pattern: str,
    path: str = ".",
    glob: str = None,
    ignore_case: bool = False,
    multiline: bool = False
)
```

##### ast
AST-aware code structure search.

```python
ast(
    pattern: str,
    path: str,
    line_number: bool = False,
    ignore_case: bool = False
)
```

#### Interactive Development

##### notebook
Multi-language notebook operations.

```python
notebook(
    action: str,  # create, read, write, execute, step, debug
    path: str = None,
    cell_type: str = None,
    content: str = None,
    kernel: str = None,
    cell_id: str = None
)
```

**Actions:**
- `create`: Create new notebook
- `read`: Read notebook or cell
- `write`: Write to cell
- `execute`: Run cell
- `step`: Step through execution
- `debug`: Start debugger

##### repl
Interactive REPL sessions.

```python
repl(
    languages: List[str],
    project_dir: str = None,
    share_context: bool = True
)
```

##### lsp
Language Server Protocol operations.

```python
lsp(
    action: str,  # initialize, definition, references, rename, diagnostics
    file: str,
    line: int = None,
    character: int = None,
    new_name: str = None
)
```

#### AI Tools

##### agent
Delegate tasks to AI agents.

```python
agent(
    prompts: List[str],
    parallel: bool = False,
    model: str = None
)
```

##### consensus
Get agreement from multiple LLMs.

```python
consensus(
    prompt: str,
    providers: List[str],
    threshold: float = 0.8
)
```

##### critic
Automated code review and quality checks.

```python
critic(analysis: str)
```

##### think
Structured reasoning workspace.

```python
think(thought: str)
```

#### System Tools

##### bash
Execute shell commands.

```python
bash(
    command: str,
    cwd: str = None,
    env: Dict = None,
    timeout: int = None
)
```

##### git
Git operations with integrated search.

```python
git(
    *args,  # git command arguments
    search: bool = False,
    pattern: str = None
)
```

##### process
Manage background processes.

```python
process(
    action: str,  # list, kill, logs
    id: str = None,
    lines: int = 100
)
```

#### Project Management

##### todo
Task management.

```python
todo(
    content: str = None,
    action: str = "list",  # list, add, update, remove
    id: str = None,
    status: str = None,
    priority: str = None
)
```

##### rules
Read project preferences.

```python
rules(path: str = ".")
```

### MCP Server Management

##### mcp
Manage external MCP servers.

```python
mcp(
    action: str,  # add, remove, list, stats
    url: str = None,
    alias: str = None
)
```

---

## Example Use Cases

### 1. Interactive Development Session

```python
# Start a multi-language notebook
notebook(action="create", path="analysis.ipynb", kernels=["python3", "javascript"])

# Write and execute Python code
notebook(
    action="write",
    cell_type="code",
    content="""
import pandas as pd
data = pd.read_csv('data.csv')
print(data.head())
""",
    kernel="python3"
)

# Execute the cell
notebook(action="execute", cell_id="cell_1")

# Debug if needed
debugger(notebook="analysis.ipynb", cell_id="cell_1", breakpoint=3)
```

### 2. Multi-Agent Code Review

```python
# Find all Python files
find(pattern="*.py", path="src/")

# Delegate review to multiple agents
agent(
    prompts=[
        "Review src/auth.py for security vulnerabilities",
        "Check src/database.py for SQL injection risks",
        "Analyze src/api.py for rate limiting implementation"
    ],
    parallel=True
)

# Get consensus on critical changes
consensus(
    prompt="Should we refactor the authentication system based on the review?",
    providers=["openai", "anthropic", "google"],
    threshold=0.8
)

# Apply critic for final quality check
critic(analysis="Review the proposed authentication refactoring for best practices")
```

### 3. Intelligent Code Search and Refactoring

```python
# Unified search for authentication patterns
results = search("authentication flow", enable_vector=True, enable_ast=True)

# Find all function definitions
ast(pattern="def authenticate.*", path="src/")

# Batch refactoring
batch(
    invocations=[
        {"tool": "edit", "params": {"file": "src/auth.py", "old": "old_auth", "new": "new_auth"}},
        {"tool": "edit", "params": {"file": "src/api.py", "old": "old_auth", "new": "new_auth"}},
        {"tool": "edit", "params": {"file": "tests/test_auth.py", "old": "old_auth", "new": "new_auth"}}
    ]
)

# Run tests
bash("pytest tests/")
```

### 4. Project Setup and Configuration

```python
# Read project rules
rules()

# Initialize todo list
todo("Set up authentication system")
todo("Implement rate limiting")
todo("Add comprehensive tests")

# Configure project-specific settings
mcp(action="add", url="github.com/user/custom-mcp", alias="custom")

# Set up git hooks
bash("git config core.hooksPath .github/hooks")
```

### 5. Debugging Complex Issues

```python
# Start investigation
think("User reports authentication fails intermittently. Possible causes: race condition, cache invalidation, token expiry")

# Search for related code
search("token expiry cache", enable_grep=True, enable_ast=True)

# Check logs
bash("tail -f logs/auth.log", timeout=30)

# Find recent changes
git("log", "--oneline", "-n", "20", "--", "src/auth/")

# Interactive debugging
repl(languages=["python"], project_dir=".")
```

### 6. Documentation Generation

```python
# Find all public APIs
ast(pattern="def [^_].*", path="src/api/")

# Generate documentation
agent(
    prompts=[
        "Document all public APIs in src/api/",
        "Create usage examples for each endpoint",
        "Generate OpenAPI specification"
    ]
)

# Write documentation
write(file_path="API_DOCUMENTATION.md", content=generated_docs)
```

---

## Troubleshooting Guide

### Common Issues and Solutions

#### 1. Installation Issues

**Problem**: `uvx hanzo-mcp` fails with "command not found"
```bash
# Solution: Install uv first
curl -LsSf https://astral.sh/uv/install.sh | sh

# Or use pip
pip install hanzo-mcp
```

**Problem**: Python version error
```bash
# Solution: Ensure Python 3.12+
python --version

# Use pyenv to install newer Python
pyenv install 3.12.0
pyenv local 3.12.0
```

#### 2. Configuration Issues

**Problem**: Tools not working as expected
```bash
# Check configuration
hanzo-mcp config show

# Verify tool is enabled
hanzo-mcp config get enabled_tools.agent

# Enable specific tool
hanzo-mcp config set enabled_tools.agent true
```

**Problem**: Permission denied errors
```bash
# Add path to allowed_paths
hanzo-mcp config add allowed_paths "/path/to/project"

# Or set via environment
export HANZO_MCP_ALLOWED_PATHS="/home/user/projects,/tmp"
```

#### 3. API Key Issues

**Problem**: Agent tools not working
```bash
# Set API keys
export OPENAI_API_KEY="sk-..."
export ANTHROPIC_API_KEY="sk-ant-..."

# Or use Hanzo API key
export HANZO_API_KEY="hanzo-..."

# Verify in config
hanzo-mcp config get agent.api_key
```

#### 4. Memory Issues

**Problem**: High memory usage with large projects
```bash
# Limit search depth
search(pattern="term", max_results=20)

# Clear vector store cache
hanzo-mcp cache clear

# Reduce chunk size
hanzo-mcp config set vector_store.chunk_size 500
```

#### 5. Network Issues

**Problem**: MCP server connection failures
```bash
# Check server status
hanzo-mcp --health

# Restart server
hanzo-mcp restart

# Use different port
hanzo-mcp --port 9999
```

#### 6. Tool-Specific Issues

**LSP not working**:
```bash
# Install language server
npm install -g typescript-language-server
pip install python-lsp-server

# Reinitialize
lsp(action="initialize", language="python")
```

**Git search not finding results**:
```bash
# Ensure git repository
git init

# Update git index
git add .
git commit -m "Initial commit"
```

### Debugging Commands

```bash
# Enable debug logging
export HANZO_MCP_LOG_LEVEL=DEBUG
hanzo-mcp --debug

# Check server logs
tail -f ~/.config/hanzo/logs/mcp-server.log

# Test specific tool
hanzo-mcp test-tool read --file README.md

# Health check
hanzo-mcp --health

# Version information
hanzo-mcp --version --verbose
```

### Getting Help

1. **Check Documentation**: https://mcp.hanzo.ai
2. **GitHub Issues**: https://github.com/hanzoai/mcp/issues
3. **Discord Community**: https://discord.gg/hanzoai
4. **Email Support**: support@hanzo.ai

---

## Architecture Overview

### System Architecture

```
┌─────────────────────────────────────────────────┐
│                 Client Applications              │
│  (Claude Desktop, VS Code, Custom Clients)       │
└─────────────────┬───────────────────────────────┘
                  │
                  │ MCP Protocol (JSON-RPC)
                  ▼
┌─────────────────────────────────────────────────┐
│              Hanzo MCP Server                    │
│  ┌──────────────────────────────────────────┐   │
│  │          Core Engine                      │   │
│  │  - Request Router                         │   │
│  │  - Tool Registry                          │   │
│  │  - Permission Manager                     │   │
│  │  - Session Manager                        │   │
│  └──────────────────────────────────────────┘   │
│                                                  │
│  ┌──────────────────────────────────────────┐   │
│  │           Tool Ecosystem                  │   │
│  │  ┌────────┐ ┌────────┐ ┌────────┐       │   │
│  │  │ File   │ │ Search │ │ Agent  │  ...  │   │
│  │  │ Tools  │ │ Tools  │ │ Tools  │       │   │
│  │  └────────┘ └────────┘ └────────┘       │   │
│  └──────────────────────────────────────────┘   │
│                                                  │
│  ┌──────────────────────────────────────────┐   │
│  │         External Services                 │   │
│  │  - LLM Providers (OpenAI, Anthropic)     │   │
│  │  - Language Servers (LSP)                │   │
│  │  - Vector Stores                         │   │
│  │  - Other MCP Servers                     │   │
│  └──────────────────────────────────────────┘   │
└─────────────────────────────────────────────────┘
```

### Tool Categories

1. **File Operations**: read, write, edit, multi_edit
2. **Search & Intelligence**: search, grep, ast, symbols
3. **Interactive Development**: notebook, repl, debugger, lsp
4. **AI & Automation**: agent, consensus, critic, think
5. **System & Process**: bash, git, process, npx, uvx
6. **Project Management**: todo, rules, palette
7. **Data & Analytics**: vector, sql, graph, stats
8. **MCP Ecosystem**: mcp, batch

### Security Model

- **Path-based permissions**: Allowed paths configuration
- **Tool-level permissions**: Enable/disable specific tools
- **Trusted servers**: Whitelist for external MCP servers
- **API key management**: Secure storage and rotation
- **Audit logging**: All operations are logged

---

## Advanced Topics

### Creating Custom Tools

```python
# Create custom_tool.py
from hanzo_mcp.tools import register_tool

@register_tool(
    name="my_custom_tool",
    description="My custom tool description",
    category="custom"
)
async def my_custom_tool(param1: str, param2: int = 10):
    """Custom tool implementation."""
    # Tool logic here
    return {"result": f"Processed {param1} with {param2}"}

# Register in config
{
  "custom_tools": {
    "my_custom_tool": {
      "module": "custom_tool",
      "enabled": true
    }
  }
}
```

### Extending with MCP Servers

```bash
# Add external MCP server
hanzo-mcp mcp add --url github.com/user/their-mcp --alias their

# Use in workflow
their_tool(action="custom", params={...})

# Chain multiple servers
batch(
    invocations=[
        {"tool": "hanzo_search", "params": {...}},
        {"tool": "their_tool", "params": {...}},
        {"tool": "another_server_tool", "params": {...}}
    ]
)
```

### Performance Optimization

```python
# Parallel execution
batch(
    invocations=[...],
    parallel=True,
    max_workers=8
)

# Caching strategies
search(
    pattern="term",
    cache=True,
    cache_ttl=3600
)

# Resource limits
{
  "performance": {
    "max_file_size": "100MB",
    "max_search_results": 100,
    "command_timeout": 60,
    "max_parallel_tools": 5
  }
}
```

### Integration Patterns

#### VS Code Integration
```json
// .vscode/settings.json
{
  "hanzo.mcp.enabled": true,
  "hanzo.mcp.server": "stdio",
  "hanzo.mcp.tools": ["read", "write", "search", "lsp"]
}
```

#### CI/CD Integration
```yaml
# .github/workflows/hanzo.yml
name: Hanzo MCP Analysis
on: [push, pull_request]
jobs:
  analyze:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      - name: Run Hanzo Analysis
        run: |
          uvx hanzo-mcp critic "Review PR changes"
          uvx hanzo-mcp test "Run comprehensive tests"
```

#### Docker Integration
```dockerfile
FROM python:3.12-slim
RUN pip install hanzo-mcp
COPY . /app
WORKDIR /app
CMD ["hanzo-mcp", "serve", "--host", "0.0.0.0"]
```

---

## Appendix

### Environment Variables Reference

| Variable | Description | Default |
|----------|-------------|---------|
| `HANZO_MCP_HOST` | Server host | 127.0.0.1 |
| `HANZO_MCP_PORT` | Server port | 8888 |
| `HANZO_MCP_LOG_LEVEL` | Logging level | INFO |
| `HANZO_MCP_PROJECT_DIR` | Project directory | . |
| `HANZO_MCP_ALLOWED_PATHS` | Comma-separated allowed paths | ~ |
| `HANZO_MCP_DISABLED_TOOLS` | Comma-separated disabled tools | |
| `OPENAI_API_KEY` | OpenAI API key | |
| `ANTHROPIC_API_KEY` | Anthropic API key | |
| `HANZO_API_KEY` | Hanzo API key | |

### Tool Compatibility Matrix

| Tool | Claude | VS Code | Custom Client | Requires API Key |
|------|--------|---------|---------------|------------------|
| read/write/edit | ✅ | ✅ | ✅ | ❌ |
| search/grep/ast | ✅ | ✅ | ✅ | ❌ |
| notebook/repl | ✅ | ✅ | ✅ | ❌ |
| agent/consensus | ✅ | ✅ | ✅ | ✅ |
| critic/think | ✅ | ✅ | ✅ | ⚠️ |
| bash/git | ✅ | ✅ | ✅ | ❌ |
| lsp | ✅ | ✅ | ✅ | ❌ |
| vector | ✅ | ✅ | ✅ | ⚠️ |

Legend: ✅ Full support | ⚠️ Optional | ❌ Not required

### Version History

- **v0.8.0** - Current version with 70+ tools
- **v0.7.0** - Added notebook and repl support
- **v0.6.0** - Introduced agent orchestration
- **v0.5.0** - LSP integration
- **v0.4.0** - Vector store support
- **v0.3.0** - Multi-MCP server support
- **v0.2.0** - Basic tool ecosystem
- **v0.1.0** - Initial release

---

## License

MIT License - See [LICENSE](https://github.com/hanzoai/mcp/blob/main/LICENSE) for details.

## Contributing

We welcome contributions! See [CONTRIBUTING.md](https://github.com/hanzoai/mcp/blob/main/CONTRIBUTING.md) for guidelines.

## Support

- Documentation: https://mcp.hanzo.ai
- GitHub: https://github.com/hanzoai/mcp
- Discord: https://discord.gg/hanzoai
- Email: support@hanzo.ai

---

*Built with ❤️ by Hanzo Industries Inc.*