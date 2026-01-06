# hanzo-consensus

Metastable consensus protocol for multi-agent agreement.

## Installation

```bash
pip install hanzo-consensus
```

## Overview

The metastable consensus protocol enables multiple AI agents to reach agreement through a two-phase process:

1. **Phase I (Sampling)**: Agents propose responses and refine based on peer feedback
2. **Phase II (Finality)**: Agreement threshold determines winner and synthesis

Reference: [github.com/luxfi/consensus](https://github.com/luxfi/consensus)

## Quick Start

```python
from hanzo_consensus import Consensus, run, State, Result

# Define execution function
async def execute(agent_id: str, prompt: str) -> Result:
    # Call your LLM here
    response = await call_llm(agent_id, prompt)
    return Result(
        id=agent_id,
        output=response,
        ok=True,
        ms=100  # Response time in ms
    )

# Run consensus
state = await run(
    prompt="What's the best approach for error handling?",
    participants=["gpt-4", "claude-3", "gemini"],
    execute=execute,
    rounds=3,
    k=3,
    alpha=0.6,
    beta_1=0.5,
    beta_2=0.8,
)

print(f"Winner: {state.winner}")
print(f"Finalized: {state.finalized}")
print(f"Synthesis: {state.synthesis}")
```

## Protocol Parameters

| Parameter | Default | Description |
|-----------|---------|-------------|
| `rounds` | 3 | Number of sampling rounds |
| `k` | 3 | Sample size per round |
| `alpha` | 0.6 | Agreement threshold (0-1) |
| `beta_1` | 0.5 | Preference threshold (Phase I) |
| `beta_2` | 0.8 | Decision threshold (Phase II) |

### Parameter Tuning

**Higher `rounds`**: More refinement, better consensus, slower
```python
run(..., rounds=5)  # More thorough consensus
```

**Higher `k`**: More peers sampled, broader agreement
```python
run(..., k=5)  # Sample more peers per round
```

**Higher `beta_2`**: Stricter finality requirement
```python
run(..., beta_2=0.9)  # Require strong agreement
```

## Classes

### Result

Represents a participant's response:

```python
@dataclass
class Result:
    id: str                   # Participant ID
    output: str               # Response text
    ok: bool                  # Success flag
    error: Optional[str]      # Error message if failed
    ms: int = 0               # Response time (affects luminance)
    round: int = 0            # Round number
```

### State

Consensus state throughout the protocol:

```python
@dataclass
class State:
    prompt: str                           # Original query
    participants: List[str]               # Participant IDs
    rounds: int                           # Total rounds
    k: int                                # Sample size
    alpha: float                          # Agreement threshold
    beta_1: float                         # Preference threshold
    beta_2: float                         # Decision threshold

    # State (updated during protocol)
    responses: Dict[str, List[str]]       # Responses per participant
    confidence: Dict[str, float]          # Confidence scores
    luminance: Dict[str, float]           # Performance scores
    finalized: bool                       # Whether consensus reached
    winner: Optional[str]                 # Winning participant
    synthesis: Optional[str]              # Final synthesized response
```

### Consensus

Main consensus class:

```python
consensus = Consensus(
    participants=["agent-1", "agent-2", "agent-3"],
    execute=my_execute_fn,
    rounds=3,
    k=3,
    alpha=0.6,
    beta_1=0.5,
    beta_2=0.8,
)

state = await consensus.run("Your question here")
```

## MCP Mesh Integration

For MCP-based agents, use the MCPMesh:

```python
from hanzo_consensus import MCPMesh, MCPAgent, run_mcp_consensus

# Create MCP agents
agents = [
    MCPAgent(id="agent-1", endpoint="http://localhost:8001"),
    MCPAgent(id="agent-2", endpoint="http://localhost:8002"),
]

# Create mesh
mesh = MCPMesh(agents)

# Run consensus through MCP
state = await run_mcp_consensus(
    mesh=mesh,
    prompt="Design an API for user authentication",
    rounds=3,
)
```

## Protocol Flow

```
┌─────────────────────────────────────────────────────────────┐
│                     PHASE I: SAMPLING                        │
├─────────────────────────────────────────────────────────────┤
│  Round 0: Initial Proposals                                  │
│    Agent-1 ───► "Use try/except blocks..."                  │
│    Agent-2 ───► "Implement error types..."                  │
│    Agent-3 ───► "Use Result types..."                       │
│                                                              │
│  Round 1-N: Refinement                                       │
│    Sample k peers (weighted by luminance)                    │
│    Share peer responses as context                           │
│    Each agent refines response                               │
│    Update confidence scores                                  │
│                                                              │
│    if max(confidence) >= β₁: proceed to Phase II            │
├─────────────────────────────────────────────────────────────┤
│                     PHASE II: FINALITY                       │
├─────────────────────────────────────────────────────────────┤
│  Calculate final scores: confidence × luminance              │
│  Winner = agent with highest score                           │
│  if score >= β₂: finalized = True                           │
│  Synthesis = winner's final response                         │
└─────────────────────────────────────────────────────────────┘
```

## Key Concepts

### Luminance

Luminance measures agent performance based on response time:

```python
luminance = 1.0 / (1.0 + response_time_ms / 1000.0)
```

Faster agents get higher luminance, increasing their influence in peer sampling.

### Confidence

Confidence measures agreement with sampled peers:

```python
confidence = previous_confidence * 0.5 + current_agreement * 0.5
```

Agreement is calculated using word overlap (Jaccard similarity).

### Finalization

Consensus is finalized when the winner's combined score exceeds β₂:

```python
score = confidence * luminance
finalized = score >= beta_2
```

## Example: Multi-LLM Consensus

```python
import asyncio
from hanzo_consensus import run, Result

async def call_openai(prompt: str) -> str:
    # Your OpenAI API call
    ...

async def call_anthropic(prompt: str) -> str:
    # Your Anthropic API call
    ...

async def call_google(prompt: str) -> str:
    # Your Google API call
    ...

PROVIDERS = {
    "openai": call_openai,
    "anthropic": call_anthropic,
    "google": call_google,
}

async def execute(agent_id: str, prompt: str) -> Result:
    import time
    start = time.time()
    try:
        output = await PROVIDERS[agent_id](prompt)
        return Result(
            id=agent_id,
            output=output,
            ok=True,
            ms=int((time.time() - start) * 1000),
        )
    except Exception as e:
        return Result(
            id=agent_id,
            output="",
            ok=False,
            error=str(e),
        )

async def main():
    state = await run(
        prompt="What's the most efficient way to sort a list in Python?",
        participants=list(PROVIDERS.keys()),
        execute=execute,
    )

    print(f"Consensus reached: {state.finalized}")
    print(f"Winner: {state.winner}")
    print(f"Answer: {state.synthesis}")

asyncio.run(main())
```

## Best Practices

1. **Diverse Participants**: Use different LLM providers for better consensus
2. **Appropriate Rounds**: Start with 3 rounds, increase for complex queries
3. **Tune Thresholds**: Lower β₂ for faster consensus, higher for stricter agreement
4. **Handle Failures**: Always check `result.ok` in your execute function
5. **Monitor Latency**: Response time affects luminance and peer selection
