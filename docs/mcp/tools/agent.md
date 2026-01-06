# Agent Tools

Multi-agent orchestration with CLI integration.

→ **Full documentation: [../../tools/agent.md](../../tools/agent.md)**

## Quick Reference

```python
# Run agent
agent(action="run", name="claude", prompt="Explain this code")

# List available agents
agent(action="list")

# Multi-agent consensus
agent(action="consensus", prompt="Design an API", agents=["claude", "gemini"])
```

Available agents: `claude`, `codex`, `gemini`, `grok`, `qwen`, `vibe`, `code`, `dev`
