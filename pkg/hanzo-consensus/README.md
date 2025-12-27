# hanzo-consensus

Metastable consensus protocol for multi-agent agreement.

## Install

```bash
pip install hanzo-consensus
```

## Basic Usage

```python
import asyncio
from hanzo_consensus import run, Result

async def execute(participant: str, prompt: str) -> Result:
    output = await call_agent(participant, prompt)
    return Result(id=participant, output=output, ok=True, ms=100)

async def main():
    state = await run(
        prompt="What is the best approach?",
        participants=["agent1", "agent2", "agent3"],
        execute=execute,
        rounds=3,
    )
    print(f"Winner: {state.winner}")
    print(f"Synthesis: {state.synthesis}")

asyncio.run(main())
```

## MCP Mesh - Agent-to-Agent Consensus

Each agent in consensus is available as MCP to every other:

```python
from hanzo_consensus import MCPMesh, run_mcp_consensus

# Create mesh of agents
mesh = MCPMesh()
mesh.register("claude", claude_server)
mesh.register("gpt4", gpt4_server)
mesh.register("gemini", gemini_server)

# Run 10 rounds of discussion
state = await run_mcp_consensus(
    mesh=mesh,
    prompt="Discuss the architecture",
    rounds=10,
)

# Access discussion history
for i, round_responses in enumerate(state.discussion_history):
    print(f"Round {i+1}:")
    for agent, response in round_responses.items():
        print(f"  [{agent}]: {response[:100]}...")
```

### MCPMesh Features

- **Agent Registration**: Local FastMCP servers or remote endpoints
- **Tool Calling**: Any agent can call tools on any other agent
- **Broadcasting**: Call a tool on all agents simultaneously
- **Discussion Rounds**: Agents build on each other's responses

```python
# Call tool on specific agent
result = await mesh.call("claude", "gpt4", "think", prompt="What do you think?")

# Broadcast to all agents
results = await mesh.broadcast("claude", "discuss", prompt="New proposal...")
```

## Protocol

Two-phase finality:

**Phase I (Sampling)**
- Each participant proposes initial response
- k-peer sampling per round
- Luminance-weighted selection (faster = higher weight)
- Confidence accumulation toward β₁

**Phase II (Finality)**
- Threshold aggregation
- β₂ finality threshold
- Winner synthesis

## Parameters

| Param | Default | Description |
|-------|---------|-------------|
| `rounds` | 3 | Sampling rounds |
| `k` | 3 | Sample size per round |
| `alpha` | 0.6 | Agreement threshold |
| `beta_1` | 0.5 | Preference threshold (Phase I) |
| `beta_2` | 0.8 | Decision threshold (Phase II) |

## Reference

https://github.com/luxfi/consensus
