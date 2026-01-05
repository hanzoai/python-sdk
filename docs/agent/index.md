# Hanzo Agent SDK

!!! note "Documentation"
    For full Agent SDK documentation, see the [detailed docs](agents.md).

The Hanzo Agent SDK enables building agentic AI applications with a lightweight, production-ready framework.

## Quick Start

```python
from agents import Agent, Runner

agent = Agent(
    name="assistant",
    instructions="You are a helpful assistant."
)

result = Runner.run_sync(agent, "Hello!")
print(result.final_output)
```

## Core Concepts

- **Agents** - LLMs configured with instructions and tools
- **Handoffs** - Allow agents to delegate to other agents
- **Guardrails** - Validate agent inputs and outputs
- **Tracing** - Built-in observability

## Navigation

- [Agents](agents.md) - Creating and configuring agents
- [Running Agents](running_agents.md) - Execution patterns
- [Tools](tools.md) - Adding tools to agents
- [Handoffs](handoffs.md) - Multi-agent coordination
- [Tracing](tracing.md) - Observability and debugging
