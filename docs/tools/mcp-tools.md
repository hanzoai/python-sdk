# MCP Management Tools

The MCP tools (`hanzo-tools-mcp`) provide management capabilities for MCP (Model Context Protocol) servers and configurations.

## Overview

These tools allow you to manage MCP server connections, add new servers, remove servers, and monitor statistics.

## mcp - Server Management

The main MCP management tool:

```python
# List configured MCP servers
mcp(action="list")

# Get server status
mcp(action="status")

# Get specific server info
mcp(action="info", server_name="filesystem")

# Restart a server
mcp(action="restart", server_name="browser")
```

### Actions

| Action | Description |
|--------|-------------|
| `list` | List all configured servers |
| `status` | Show running status of servers |
| `info` | Get detailed server information |
| `restart` | Restart a specific server |

## mcp_add - Add Servers

Add new MCP server configurations:

```python
# Add stdio server
mcp_add(
    name="my-server",
    command="uvx my-mcp-server",
    transport="stdio"
)

# Add SSE server
mcp_add(
    name="remote-server",
    url="http://localhost:8080/sse",
    transport="sse"
)

# Add with environment variables
mcp_add(
    name="api-server",
    command="node server.js",
    env={"API_KEY": "secret123"}
)

# Add with arguments
mcp_add(
    name="custom-server",
    command="python",
    args=["-m", "my_mcp", "--port", "9000"]
)
```

### Parameters

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `name` | str | required | Server identifier |
| `command` | str | - | Command to spawn server |
| `url` | str | - | URL for SSE/HTTP transport |
| `transport` | str | `stdio` | `stdio`, `sse`, `http` |
| `args` | list | - | Additional command arguments |
| `env` | dict | - | Environment variables |

## mcp_remove - Remove Servers

Remove MCP server configurations:

```python
# Remove by name
mcp_remove(name="old-server")

# Remove with confirmation
mcp_remove(name="important-server", confirm=True)
```

### Parameters

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `name` | str | required | Server to remove |
| `confirm` | bool | `False` | Require confirmation |

## mcp_stats - Statistics

Get MCP usage statistics:

```python
# Overall statistics
mcp_stats()

# Per-server statistics
mcp_stats(server_name="filesystem")

# Stats for time period
mcp_stats(period="1h")
```

### Output

```
MCP Statistics
==============

Servers: 5 configured, 4 running

Tool Calls (last hour):
  filesystem: 142 calls
  browser: 38 calls
  shell: 256 calls
  memory: 24 calls

Errors: 3 total
  - filesystem: 1 (permission denied)
  - browser: 2 (timeout)
```

## Transport Types

| Transport | Use Case | Requirements |
|-----------|----------|--------------|
| `stdio` | Local servers | Executable command |
| `sse` | Remote servers | HTTP endpoint |
| `http` | Streamable HTTP | HTTP endpoint |

### stdio Transport

Spawns server as subprocess:

```python
mcp_add(
    name="local",
    command="uvx hanzo-mcp",
    transport="stdio"
)
```

### SSE Transport

Connects to Server-Sent Events endpoint:

```python
mcp_add(
    name="remote",
    url="http://api.example.com/mcp/sse",
    transport="sse"
)
```

### HTTP Transport

Streamable HTTP transport:

```python
mcp_add(
    name="http-server",
    url="http://localhost:8080/mcp",
    transport="http"
)
```

## Installation

```bash
pip install hanzo-tools-mcp
```

## Configuration File

MCP servers are typically configured in:
- `~/.config/hanzo/mcp.json` (global)
- `.hanzo/mcp.json` (project-local)

Example configuration:

```json
{
  "servers": {
    "filesystem": {
      "command": "uvx hanzo-tools-fs",
      "transport": "stdio"
    },
    "browser": {
      "command": "uvx hanzo-tools-browser",
      "transport": "stdio",
      "env": {
        "BROWSER_HEADLESS": "true"
      }
    }
  }
}
```

## Best Practices

### 1. Use Environment Variables for Secrets

```python
mcp_add(
    name="api-server",
    command="my-server",
    env={"API_KEY": "${API_KEY}"}  # Reference from environment
)
```

### 2. Group Related Servers

Organize servers by function:

```python
# Development servers
mcp_add(name="dev-db", command="...")
mcp_add(name="dev-cache", command="...")

# Production servers (separate config)
mcp_add(name="prod-db", command="...", env={"ENV": "production"})
```

### 3. Monitor Statistics

```python
# Regular health checks
stats = mcp_stats()
if stats.error_count > threshold:
    alert("MCP errors detected")
```

### 4. Use Local Config for Projects

```python
# Project-specific servers in .hanzo/mcp.json
mcp_add(
    name="project-specific",
    command="./scripts/mcp-server.sh",
    config_path=".hanzo/mcp.json"
)
```
