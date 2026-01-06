# MCP Configuration

Comprehensive configuration options for hanzo-mcp.

## Configuration Sources

Configuration is loaded in order of precedence (highest first):

1. CLI arguments
2. Environment variables
3. Project config (`.hanzo/config.json`)
4. Global config (`~/.config/hanzo/mcp-settings.json`)
5. Default settings

## CLI Options

```bash
hanzo-mcp [OPTIONS]

Options:
  --transport [stdio|sse]     Transport mode (default: stdio)
  --host TEXT                 Host for SSE server (default: 127.0.0.1)
  --port INTEGER              Port for SSE server (default: 8888)
  --allow-path PATH           Allowed file system paths (repeatable)
  --project-path PATH         Project paths for context (repeatable)
  --project-dir PATH          Project root directory
  --command-timeout FLOAT     Command timeout in seconds (default: 30)
  --disable-write-tools       Disable file write operations
  --disable-search-tools      Disable search operations
  --install                   Install Claude Desktop configuration
  --dev                       Enable development mode
  --version                   Show version
  --help                      Show help
```

## Environment Variables

### Core Settings

| Variable | Default | Description |
|----------|---------|-------------|
| `HANZO_MCP_TRANSPORT` | `stdio` | Transport mode |
| `HANZO_MCP_HOST` | `127.0.0.1` | SSE server host |
| `HANZO_MCP_PORT` | `8888` | SSE server port |
| `HANZO_AUTO_BACKGROUND_TIMEOUT` | `30` | Command auto-background timeout (seconds) |
| `HANZO_DEFAULT_SHELL` | `zsh` | Default shell for commands |

### Agent Settings

| Variable | Default | Description |
|----------|---------|-------------|
| `HANZO_AGENT_MODEL` | - | Default model for agent tools |
| `HANZO_AGENT_API_KEY` | - | API key for agent |
| `HANZO_AGENT_BASE_URL` | - | Custom API base URL |
| `HANZO_AGENT_MAX_ITERATIONS` | `10` | Max agent iterations |
| `HANZO_AGENT_MAX_TOOL_USES` | `30` | Max tool uses per run |

### LLM API Keys

| Variable | Description |
|----------|-------------|
| `OPENAI_API_KEY` | OpenAI API key |
| `ANTHROPIC_API_KEY` | Anthropic API key |
| `TOGETHER_API_KEY` | Together AI API key |
| `GROQ_API_KEY` | Groq API key |

## Config File Format

### Global Config

Location: `~/.config/hanzo/mcp-settings.json`

```json
{
  "server": {
    "name": "hanzo-mcp",
    "host": "127.0.0.1",
    "port": 8888,
    "transport": "stdio"
  },
  "tools": {
    "command_timeout": 30,
    "disable_write_tools": false,
    "disable_search_tools": false
  },
  "paths": {
    "allowed": ["~"],
    "project": []
  },
  "agent": {
    "enabled": true,
    "model": "claude-3-5-sonnet-20241022",
    "max_iterations": 10,
    "max_tool_uses": 30
  },
  "mcp_servers": []
}
```

### Project Config

Location: `.hanzo/config.json` in project root

```json
{
  "name": "my-project",
  "enabled_tools": {
    "browser": true,
    "database": false
  },
  "disabled_tools": ["vector"],
  "rules": [
    "Use TypeScript for all new files",
    "Follow existing code style"
  ]
}
```

## Tool Configuration

### Enable/Disable Tools

```json
{
  "tools": {
    "enabled": ["shell", "filesystem", "memory", "reasoning"],
    "disabled": ["browser", "database", "vector"]
  }
}
```

### Tool-Specific Settings

```json
{
  "tools": {
    "shell": {
      "default_shell": "zsh",
      "timeout": 30
    },
    "browser": {
      "headless": true,
      "default_viewport": "desktop"
    },
    "memory": {
      "scope": "project"
    }
  }
}
```

## Security

### Path Restrictions

By default, the server restricts file access. Use `--allow-path` to grant access:

```bash
# Allow home directory
hanzo-mcp --allow-path ~

# Allow specific project
hanzo-mcp --allow-path /path/to/project

# Allow multiple paths
hanzo-mcp --allow-path ~/work --allow-path /tmp
```

### Disable Dangerous Tools

```bash
# Read-only mode
hanzo-mcp --disable-write-tools

# No search (for sensitive codebases)
hanzo-mcp --disable-search-tools
```

## Claude Desktop Integration

### Auto-Install

```bash
hanzo-mcp --install
```

This creates the configuration at:
- macOS: `~/Library/Application Support/Claude/claude_desktop_config.json`
- Windows: `%APPDATA%\Claude\claude_desktop_config.json`
- Linux: `~/.config/claude/claude_desktop_config.json`

### Manual Configuration

```json
{
  "mcpServers": {
    "hanzo": {
      "command": "uvx",
      "args": ["hanzo-mcp", "--allow-path", "~"]
    }
  }
}
```

## Debugging

### Enable Verbose Logging

```bash
# SSE mode (logging visible)
hanzo-mcp --transport sse

# Check version and config
hanzo-mcp --version
```

### View Running Processes

Once connected, use the `ps` tool:

```
ps()           # List all background processes
ps(logs="id")  # View process output
```
