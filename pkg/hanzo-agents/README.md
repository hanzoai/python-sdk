# hanzo-agents

Multi-agent orchestration CLI for Hanzo AI.

## Installation

```bash
# Install via uv
uv tool install hanzo-agents

# Or via pip
pip install hanzo-agents
```

## Usage

```bash
# Run an agent
hanzo-agents run claude "Explain this code"
hanzo-agents run gemini "Review this PR"

# List available agents
hanzo-agents list

# Check agent status
hanzo-agents status
hanzo-agents status claude

# Show configuration
hanzo-agents config
```

## Available Agents

| Agent | Description |
|-------|-------------|
| `claude` | Anthropic Claude Code CLI |
| `codex` | OpenAI Codex CLI |
| `gemini` | Google Gemini CLI |
| `grok` | xAI Grok CLI |
| `qwen` | Alibaba Qwen CLI |
| `vibe` | Vibe coding agent |

## Library Usage

```python
from hanzo_agents import AgentTool
import asyncio

tool = AgentTool()
result = asyncio.run(tool.call(None, action="run", name="claude", prompt="Hello"))
print(result)
```

## License

Apache 2.0
