# hanzo-consensus

Metastable consensus protocol for multi-agent agreement.

## Install

```bash
pip install hanzo-consensus
```

## Usage

```python
import asyncio
from hanzo_consensus import Consensus, Result, run

async def execute(participant: str, prompt: str) -> Result:
    """Your execution function."""
    output = await call_agent(participant, prompt)
    return Result(id=participant, output=output, ok=True, ms=100)

async def main():
    state = await run(
        prompt="What is the best approach?",
        participants=["agent1", "agent2", "agent3"],
        execute=execute,
        rounds=3,
        k=2,
    )
    
    print(f"Winner: {state.winner}")
    print(f"Finalized: {state.finalized}")
    print(f"Synthesis: {state.synthesis}")

asyncio.run(main())
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
