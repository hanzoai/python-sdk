# Hanzo Agents SDK

Production-grade AI agent runtime for building deterministic, debuggable, and scalable agent systems.

## Overview

Hanzo Agents SDK provides nine first-class abstractions for building AI agent systems:

1. **Agents** - Encapsulate skills and tools with zero side-effects outside tool calls
2. **Tools** - Perform side-effects and mutate state in a typed, inspectable way
3. **Networks** - Orchestrate agent execution with deterministic routing
4. **State** - Strongly-typed, validated state containers
5. **Routers** - Control agent flow (deterministic or hybrid LLM-based)
6. **History** - Chronological log for replay and audit
7. **Memory** - Long-term storage (KV and vector)
8. **Models** - Unified adapter interface for any LLM
9. **Deployment** - Production-ready with telemetry, checkpointing, and scale

## Quick Start

```bash
pip install hanzo-agents[all]

# Run an example network
hanzo-agents run examples/code_fix_network.py \
              --state '{"repo":"demo"}' \
              --model claude-3-opus
```

## Core Concepts

### Agents

```python
from hanzo_agents import Agent, Tool
from typing import List

class PlanningAgent(Agent[ProjectState]):
    name = "planner"
    description = "Creates project plans"
    model = "model://anthropic/claude-3-haiku"
    
    tools: List[Tool] = [
        CreatePlanTool(),
        UpdatePlanTool(),
    ]
```

### Tools

```python
from hanzo_agents import Tool
from pydantic import BaseModel

class CreatePlanTool(Tool[ProjectState]):
    name = "create_plan"
    description = "Create a new project plan"
    
    class Parameters(BaseModel):
        tasks: List[str]
        timeline: str
    
    def handle(self, tasks: List[str], timeline: str, network):
        # Mutate state in a typed way
        network.state.plan = Plan(tasks=tasks, timeline=timeline)
        return f"Created plan with {len(tasks)} tasks"
```

### Networks & Routers

```python
from hanzo_agents import Network, State
from dataclasses import dataclass

@dataclass
class ProjectState(State):
    repo: str
    plan: Optional[Plan] = None
    tests_passed: bool = False
    done: bool = False

def project_router(network, call_count, last_result, stack):
    """Deterministic routing logic"""
    s = network.state
    if s.done or call_count > 50:
        return None
    if s.plan is None:
        return PlanningAgent
    if not s.tests_passed:
        return TestingAgent
    s.done = True
    return None

# Run the network
network = Network(
    state=ProjectState(repo="my-project"),
    agents=[PlanningAgent, TestingAgent, ReviewAgent],
    router=project_router
)
network.run()
```

### Memory

```python
# Long-term memory for context across runs
network = Network(
    state=state,
    agents=agents,
    router=router,
    memory_kv=SQLiteKV("project.db"),
    memory_vector=FAISSVector(dimension=1536)
)

# Agents can query memory
class ResearchAgent(Agent):
    async def run(self, state, history):
        # Pull relevant context
        context = await self.network.memory.vector.query(
            "previous security findings", 
            k=5
        )
        # Use in prompt...
```

## CLI

The `hanzo-agents` CLI provides:

```bash
# Basic execution
hanzo-agents run network.py --state '{"key": "value"}'

# Model configuration
hanzo-agents run network.py --model gpt-4 --model-config config.yaml

# GPU selection
hanzo-agents run network.py --cuda 0

# Observability
hanzo-agents run network.py --json-lines --port 9464  # Prometheus

# Checkpointing
hanzo-agents run network.py --checkpoint state.chkpt
hanzo-agents run network.py --restore state.chkpt
```

## Production Features

- **Type Safety**: Full typing with generics for compile-time guarantees
- **Deterministic**: Reproducible execution with explicit state mutations
- **Observable**: OpenTelemetry tracing + Prometheus metrics built-in
- **Scalable**: Horizontal scaling via stateless networks
- **Debuggable**: Step-through debugging with history replay
- **Extensible**: Plugin architecture for tools, models, and memory backends

## Architecture

```
hanzo_agents/
├── core/
│   ├── agent.py       # Agent base class and registry
│   ├── tool.py        # Tool base class and decorators  
│   ├── state.py       # State validation and guards
│   ├── router.py      # Router types and helpers
│   ├── network.py     # Main orchestration loop
│   ├── history.py     # Interaction logging
│   ├── memory.py      # Memory backends (KV, vector)
│   └── model.py       # Model adapters and registry
├── contrib/           # Optional integrations
│   ├── chromadb.py    # ChromaDB vector store
│   ├── neo4j.py       # Neo4j graph memory
│   └── langchain.py   # LangChain compatibility
├── cli.py             # CLI entry point
└── examples/          # Example networks
```

## License

MIT License - see LICENSE file for details.