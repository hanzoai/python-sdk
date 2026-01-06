# VS Code Integration

Set up hanzo-mcp with VS Code, Cursor, and other MCP-compatible editors.

## VS Code with Continue

[Continue](https://continue.dev) is an open-source AI code assistant that supports MCP.

### Installation

1. Install Continue extension from VS Code marketplace
2. Configure MCP in `~/.continue/config.json`:

```json
{
  "models": [...],
  "mcpServers": [
    {
      "name": "hanzo",
      "command": "uvx",
      "args": ["hanzo-mcp"]
    }
  ]
}
```

3. Restart VS Code

## Cursor

Cursor has built-in MCP support.

### Configuration

Add to Cursor settings (`~/.cursor/mcp.json`):

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

## Windsurf (Codeium)

### Configuration

Add to `~/.codeium/windsurf/mcp_config.json`:

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

## Generic MCP Client

For any MCP-compatible client:

### stdio Transport

```json
{
  "command": "uvx",
  "args": ["hanzo-mcp", "--transport", "stdio"]
}
```

### SSE Transport

Start the server:

```bash
hanzo-mcp --transport sse --port 8888
```

Connect to: `http://localhost:8888/sse`

## Project-Specific Configuration

Create `.hanzo/config.json` in your project root:

```json
{
  "name": "my-project",
  "rules": [
    "Use TypeScript",
    "Follow existing patterns"
  ],
  "enabled_tools": {
    "shell": true,
    "browser": false
  }
}
```

The MCP server will automatically detect and apply project settings.

## Recommended Extensions

### VS Code

- **Continue** - AI assistant with MCP support
- **Claude Dev** - Claude integration
- **GitLens** - Git integration (works well with hanzo tools)

### Cursor

Built-in AI features work with hanzo-mcp out of the box.

## Troubleshooting

### Server Not Starting

```bash
# Check if hanzo-mcp is installed
uvx hanzo-mcp --version

# Test manually
uvx hanzo-mcp --transport sse --port 8888
# Then open http://localhost:8888 in browser
```

### Permission Errors

Ensure paths are allowed:

```json
{
  "args": ["hanzo-mcp", "--allow-path", "/path/to/project"]
}
```

### Tool Not Available

Some tools require additional dependencies:

```bash
# Full installation with all tools
pip install hanzo-mcp[tools-all]

# Or specific tools
pip install hanzo-mcp[browser]  # Playwright
pip install hanzo-mcp[llm]      # LiteLLM
```

### Logs and Debugging

For SSE transport, logs appear in terminal. For stdio:

```bash
# Redirect stderr to file
hanzo-mcp 2>/tmp/hanzo-mcp.log
```

## Performance Tips

1. **Use uvx** - Faster startup than pip-installed version
2. **Limit paths** - Only allow necessary directories
3. **Disable unused tools** - Reduces memory usage
4. **Use project config** - Faster tool discovery

## See Also

- [Quickstart](quickstart.md) - Getting started
- [Configuration](configuration.md) - All configuration options
- [Tools Reference](../tools/index.md) - Available tools
