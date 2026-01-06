# hanzo-network

Agent network orchestration for distributed AI systems.

## Installation

```bash
pip install hanzo-network
```

## Overview

hanzo-network enables building distributed agent networks with:

- **Topology Management** - Define and manage agent network structures
- **Device Capabilities** - Track compute resources across nodes
- **Partitioning Strategies** - Distribute work across agents
- **Local LLM Support** - Run models locally for development

## Quick Start

```python
from hanzo_network.core import AgentNetwork, NetworkConfig
from hanzo_network.topology import RingMemoryWeightedPartitioningStrategy

# Create network
config = NetworkConfig(
    name="my-network",
    strategy=RingMemoryWeightedPartitioningStrategy(),
)
network = AgentNetwork(config)

# Add agents
network.add_agent("agent-1", capabilities={"memory": 16, "gpu": True})
network.add_agent("agent-2", capabilities={"memory": 8, "gpu": False})

# Route work
result = await network.route("Process this complex task")
```

## Core Components

### AgentNetwork

The main network orchestrator:

```python
from hanzo_network.core import AgentNetwork, NetworkConfig

# Configuration
config = NetworkConfig(
    name="production-network",
    max_agents=100,
    timeout=30.0,
    retry_count=3,
)

# Create network
network = AgentNetwork(config)

# Add agents
network.add_agent(
    agent_id="worker-1",
    endpoint="http://localhost:8001",
    capabilities={"memory": 32, "gpu": True, "cores": 8}
)

# Remove agents
network.remove_agent("worker-1")

# List agents
agents = network.list_agents()

# Get agent status
status = network.get_status("worker-1")
```

### Router

Route requests to appropriate agents:

```python
from hanzo_network.core import Router, RoutingStrategy

# Create router
router = Router(strategy=RoutingStrategy.ROUND_ROBIN)

# Route request
agent = router.route("Process this task")

# Available strategies
RoutingStrategy.ROUND_ROBIN      # Cycle through agents
RoutingStrategy.LEAST_LOADED     # Pick agent with lowest load
RoutingStrategy.CAPABILITY_MATCH # Match task to capabilities
RoutingStrategy.RANDOM           # Random selection
```

## Topology

### Device Capabilities

Track and match device capabilities:

```python
from hanzo_network.topology import DeviceCapabilities

# Define capabilities
caps = DeviceCapabilities(
    memory_gb=32,
    gpu_memory_gb=24,
    cpu_cores=16,
    gpu_available=True,
    gpu_model="RTX 4090",
)

# Check if capable
can_run = caps.can_handle(
    min_memory=16,
    requires_gpu=True,
)
```

### Partitioning Strategies

Distribute work across the network:

```python
from hanzo_network.topology import (
    RingMemoryWeightedPartitioningStrategy,
    PartitioningStrategy,
)

# Memory-weighted ring partitioning
strategy = RingMemoryWeightedPartitioningStrategy()

# Partition data
partitions = strategy.partition(
    data=large_dataset,
    agents=network.list_agents(),
)

# Process partitions
for agent_id, partition in partitions.items():
    await network.send(agent_id, partition)
```

## Local LLM

Run models locally for development:

```python
from hanzo_network.llm import LocalLLM

# Create local LLM
llm = LocalLLM(
    model_path="/path/to/model",
    context_size=4096,
)

# Generate response
response = await llm.generate(
    prompt="Explain quantum computing",
    max_tokens=500,
)
```

## Tools

### Memory Tool

Shared memory across the network:

```python
from hanzo_network.tools import MemoryTool

memory = MemoryTool(network)

# Store data
await memory.store("key", {"data": "value"})

# Retrieve data
data = await memory.retrieve("key")

# Search
results = await memory.search("query")
```

## Examples

### Distributed Demo

```python
from hanzo_network.core import AgentNetwork, NetworkConfig
from hanzo_network.topology import DeviceCapabilities

async def main():
    # Create network
    network = AgentNetwork(NetworkConfig(name="distributed"))

    # Add workers with capabilities
    for i in range(4):
        caps = DeviceCapabilities(
            memory_gb=16 + i * 8,
            gpu_available=i % 2 == 0,
        )
        network.add_agent(f"worker-{i}", capabilities=caps)

    # Distribute task
    task = "Process large dataset"
    results = await network.broadcast(task)

    # Aggregate results
    final = aggregate(results)
    return final
```

### Local LLM Demo

```python
from hanzo_network.llm import LocalLLM

async def main():
    # Setup local model
    llm = LocalLLM(model_path="./models/llama-7b")

    # Development queries
    response = await llm.generate("Write a Python function to sort a list")
    print(response)
```

## Configuration

### Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `HANZO_NETWORK_TIMEOUT` | `30` | Request timeout in seconds |
| `HANZO_NETWORK_RETRIES` | `3` | Max retry attempts |
| `HANZO_NETWORK_LOG_LEVEL` | `INFO` | Logging level |

### Network Config

```python
NetworkConfig(
    name="my-network",          # Network identifier
    max_agents=100,             # Maximum agents
    timeout=30.0,               # Request timeout
    retry_count=3,              # Retry attempts
    health_check_interval=60,   # Health check frequency
    load_balancing=True,        # Enable load balancing
)
```

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                      Agent Network                           │
├─────────────────────────────────────────────────────────────┤
│  ┌─────────────────┐  ┌─────────────────┐                   │
│  │     Router      │  │    Topology     │                   │
│  │                 │  │    Manager      │                   │
│  └────────┬────────┘  └────────┬────────┘                   │
│           │                    │                             │
│  ┌────────▼────────────────────▼────────┐                   │
│  │         Partitioning Strategy         │                   │
│  └──────────────────┬───────────────────┘                   │
│                     │                                        │
│  ┌──────────────────▼───────────────────┐                   │
│  │              Agent Pool               │                   │
│  │  ┌────────┐ ┌────────┐ ┌────────┐   │                   │
│  │  │Agent 1 │ │Agent 2 │ │Agent N │   │                   │
│  │  └────────┘ └────────┘ └────────┘   │                   │
│  └──────────────────────────────────────┘                   │
└─────────────────────────────────────────────────────────────┘
```

## Best Practices

1. **Capability Matching**: Define accurate device capabilities for optimal routing
2. **Health Checks**: Enable health checks to detect failed agents
3. **Retry Logic**: Configure retries for transient failures
4. **Load Balancing**: Use load-aware routing for production
5. **Local Development**: Use LocalLLM for testing without network overhead
