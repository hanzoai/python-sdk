# Agent Reference

API reference for the hanzo-agent framework.

## Overview

hanzo-agent provides a multi-agent SDK with:

- OpenAI-compatible API
- Multi-agent orchestration
- Tool use and guardrails
- Streaming and tracing

## Documentation

| Topic | Description |
|-------|-------------|
| [Getting Started](../../agent/index.md) | Introduction to agents |
| [Running Agents](../../agent/running_agents.md) | How to run agents |
| [Agent Config](../../agent/config.md) | Configuration options |
| [Tools](../../agent/tools.md) | Tool integration |
| [Guardrails](../../agent/guardrails.md) | Safety constraints |
| [Multi-Agent](../../agent/multi_agent.md) | Orchestrating multiple agents |
| [Handoffs](../../agent/handoffs.md) | Agent handoff patterns |
| [Streaming](../../agent/streaming.md) | Streaming responses |
| [Tracing](../../agent/tracing.md) | Debugging and tracing |

## Quick Start

```python
from hanzo_agent import Agent, Runner

agent = Agent(
    name="assistant",
    instructions="You are a helpful assistant.",
)

result = await Runner.run(agent, "Hello!")
print(result.final_output)
```

## See Also

- [Agent Tools](../../tools/agent.md) - CLI agent integration
- [Consensus Protocol](../../lib/consensus.md) - Multi-agent agreement
