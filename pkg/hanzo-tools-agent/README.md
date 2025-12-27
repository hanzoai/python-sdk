# hanzo-tools-agent

Agent orchestration tools for Hanzo MCP.

## Installation

```bash
pip install hanzo-tools-agent

# Optional: API mode
pip install hanzo-tools-agent[api]

# Optional: High-performance
pip install hanzo-tools-agent[perf]
```

## Tools

### agent - Unified Agent Runner
Run various AI CLI agents with auto-backgrounding.

```python
# Run with default agent
agent(action="run", prompt="Explain this code")

# Run specific agent
agent(action="run", name="gemini", prompt="Review this PR")

# List available agents
agent(action="list")

# Check agent status
agent(action="status", name="claude")
```

**Available Agents:**
- `claude` - Anthropic Claude Code CLI
- `codex` - OpenAI Codex CLI
- `gemini` - Google Gemini CLI
- `grok` - xAI Grok CLI
- `qwen` - Alibaba Qwen CLI
- `vibe` - Vibe coding agent
- `code` - Hanzo Code agent
- `dev` - Hanzo Dev agent

### Direct API Mode
Configure agents for direct API calls without CLI:

```json
// ~/.hanzo/agents/custom.json
{
    "endpoint": "https://api.openai.com/v1/chat/completions",
    "api_type": "openai",
    "model": "gpt-4",
    "env_key": "OPENAI_API_KEY"
}
```

### iching - I Ching Wisdom
```python
iching(challenge="How should I approach this refactoring?")
```

### review - Code Review
```python
review(
    focus="FUNCTIONALITY",
    work_description="Implemented auto-import feature",
    file_paths=["/path/to/file.py"]
)
```

## License

MIT
