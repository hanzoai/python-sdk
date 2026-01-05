# Quickstart

Get up and running with Hanzo Python SDK in minutes.

## 1. Install

```bash
pip install hanzo-mcp
```

## 2. Run MCP Server

### With Claude Code

```bash
uvx hanzo-mcp
```

Claude Code will auto-detect and use all 30+ tools.

### With VS Code Extension

1. Install the Hanzo extension
2. The extension auto-detects `uvx` and starts the Python MCP
3. All tools are available in the AI assistant

## 3. Use the Tools

### File Operations

```python
# Read a file
read(file_path="/path/to/file.py")

# Edit a file
edit(
    file_path="/path/to/file.py",
    old_string="old code",
    new_string="new code"
)

# Search for patterns
search(pattern="TODO", path="./src")
```

### Shell Commands

```python
# Run commands (auto-backgrounds after 45s)
cmd("npm install")

# Run in parallel
cmd(["npm install", "cargo build"], parallel=True)

# DAG execution
cmd([
    "mkdir dist",
    {"parallel": ["cp a dist/", "cp b dist/"]},
    "zip -r out.zip dist/"
])
```

### Browser Automation

```python
# Navigate to page
browser(action="navigate", url="https://example.com")

# Click element
browser(action="click", selector="button.submit")

# Take screenshot
browser(action="screenshot", full_page=True)

# Mobile emulation
browser(action="emulate", device="mobile")
```

### Memory & Reasoning

```python
# Save to memory
memory(action="create", data={"note": "Important insight"})

# Recall memories
memory(action="recall", query="project architecture")

# Structured thinking
think(thought="Analyzing the problem...")

# Critical analysis
critic(analysis="Review this implementation...")
```

## 4. Agent SDK

Build your own AI agents:

```python
from agents import Agent, Runner

# Create an agent
agent = Agent(
    name="code_reviewer",
    instructions="""
    You are a code review expert.
    Analyze code for bugs, performance issues, and best practices.
    """,
    tools=[review_code, suggest_improvements]
)

# Run the agent
result = Runner.run_sync(
    agent,
    "Review this Python function for issues..."
)

print(result.final_output)
```

### Multi-Agent Systems

```python
from agents import Agent, handoff

# Create specialized agents
security_agent = Agent(
    name="security",
    instructions="Analyze code for security vulnerabilities."
)

performance_agent = Agent(
    name="performance",
    instructions="Analyze code for performance issues."
)

# Main coordinator
lead_agent = Agent(
    name="lead",
    instructions="Coordinate code review. Handoff to specialists.",
    handoffs=[
        handoff(security_agent, "security issues"),
        handoff(performance_agent, "performance concerns")
    ]
)
```

## 5. Configuration

### Environment Variables

```bash
# Disable auto-backgrounding
export HANZO_AUTO_BACKGROUND_TIMEOUT=0

# Set allowed paths
export HANZO_ALLOWED_PATHS="/home/user/projects,/tmp"
```

### VS Code Settings

```json
{
  "hanzo.mcp.backend": "python",
  "hanzo.mcp.pythonCommand": "uvx hanzo-mcp",
  "hanzo.mcp.disableBrowserTool": false,
  "hanzo.mcp.enabledTools": ["read", "write", "cmd", "search"]
}
```

## Next Steps

- [MCP Tools Reference](../mcp/index.md) - Complete tool documentation
- [Agent SDK Guide](../agent/index.md) - Build custom AI agents
- [Configuration](../mcp/configuration.md) - Advanced configuration options
