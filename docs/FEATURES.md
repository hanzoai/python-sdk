# Hanzo AI SDK - Unified AI Features

The Hanzo AI SDK now includes integrated support for agents, MCP (Model Context Protocol), and local AI clusters, providing a complete solution for AI development that is **local, private, and free**.

## Installation

```bash
pip install hanzoai

# Optional: Install additional components
pip install hanzo-agents  # For agent networks
pip install hanzo-mcp     # For MCP tools
pip install exo-explore   # For local AI clusters
```

## Features

### 1. Local AI Clusters

Run AI models locally on your own hardware or across your network of devices:

```python
import asyncio
from hanzoai import cluster

async def run_local_ai():
    # Start a local cluster
    my_cluster = await cluster.start_local_cluster(
        name="my-ai-cluster",
        model_path="~/.cache/huggingface/hub"
    )
    
    # Run inference locally
    result = await my_cluster.inference(
        prompt="Hello, local AI!",
        model="llama-3.2-3b"
    )
    
    print(result)
    await my_cluster.stop()

asyncio.run(run_local_ai())
```

### 2. Agent Networks

Create sophisticated AI agent systems with local and distributed execution:

```python
from hanzoai import agents

# Create agents
local_agent = agents.create_agent(
    name="local-assistant",
    model="llama-3.2-3b",
    base_url="http://localhost:8000"  # Local cluster
)

cloud_agent = agents.create_agent(
    name="cloud-assistant",
    model="anthropic/claude-3-5-sonnet-20241022"
)

# Create a network
network = agents.create_network(
    agents=[local_agent, cloud_agent],
    router=agents.state_based_router()  # Smart routing
)

# The network automatically routes tasks to the best agent
result = await network.run("Complex task requiring analysis")
```

### 3. MCP Tools

Access 70+ tools through the Model Context Protocol:

```python
from hanzoai import mcp

# Create an MCP server
server = mcp.create_mcp_server(
    name="my-tools",
    allowed_paths=[".", "/workspace"],
    enable_agent_tool=True
)

# Or connect to an existing MCP server
client = mcp.MCPClient()
await client.connect()

# Use tools
result = await client.call_tool(
    "search",
    pattern="def main",
    path="."
)
```

### 4. Mining Network

Contribute compute to the network and earn rewards:

```python
from hanzoai import cluster

# Join the mining network
miner = await cluster.join_mining_network(
    wallet_address="0x1234...",
    max_ram=8,  # GB
    max_vram=4  # GB
)

# Check mining stats
stats = miner.get_stats()
print(f"Compute contributed: {stats['compute_contributed']}")
print(f"Rewards earned: {stats['rewards_earned']}")
```

## Architecture

```
┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐
│   Local AI      │     │  Agent Networks │     │   MCP Tools     │
│   Cluster       │────▶│                 │────▶│                 │
│  (exo-based)    │     │  (hanzo-agents) │     │  (hanzo-mcp)    │
└─────────────────┘     └─────────────────┘     └─────────────────┘
         │                       │                        │
         └───────────────────────┴────────────────────────┘
                                 │
                      ┌──────────▼──────────┐
                      │    Hanzo AI SDK     │
                      │    (unified API)    │
                      └─────────────────────┘
```

## Use Cases

### 1. **Cost-Effective Development**
Use local models for development and testing, only using cloud APIs when necessary:

```python
# Development: Use local cluster
dev_result = await local_cluster.inference("Test prompt")

# Production: Use cloud with same interface
prod_result = completion(model="gpt-4", messages=[...])
```

### 2. **Privacy-First Applications**
Keep sensitive data local while still leveraging AI:

```python
# Process sensitive documents locally
local_agent = agents.create_agent(
    name="privacy-agent",
    model="llama-3.2-3b",
    base_url="http://localhost:8000"
)

result = await local_agent.process_documents(
    documents=sensitive_files,
    keep_local=True
)
```

### 3. **Distributed AI Workloads**
Distribute work across multiple devices:

```python
# Create a cluster across your devices
cluster_config = cluster.ClusterConfig(
    broadcast_addresses=[
        "192.168.1.100",  # Desktop
        "192.168.1.101",  # Laptop
        "192.168.1.102",  # Server
    ]
)

distributed_cluster = cluster.HanzoCluster(cluster_config)
await distributed_cluster.start()
```

## Best Practices

1. **Start Local**: Always try local models first for cost savings
2. **Smart Routing**: Use agent networks to automatically route between local and cloud
3. **Cache Models**: Download and cache models locally for offline use
4. **Join Mining**: Contribute unused compute to earn rewards
5. **Use MCP**: Leverage the extensive tool ecosystem

## Environment Variables

```bash
# Local cluster configuration
HANZO_CLUSTER_NAME=my-cluster
HANZO_MODEL_PATH=~/.cache/huggingface/hub

# Mining configuration  
HANZO_WALLET_ADDRESS=0x1234...
HANZO_MAX_RAM=16
HANZO_MAX_VRAM=8

# Agent configuration
HANZO_DEFAULT_MODEL=llama-3.2-3b
HANZO_FALLBACK_MODEL=anthropic/claude-3-5-sonnet-20241022
```

## Roadmap

- [ ] Automatic model downloading and management
- [ ] Peer-to-peer model sharing
- [ ] Federated learning support
- [ ] Mobile device support
- [ ] Enhanced mining rewards system
- [ ] Native GUI for cluster management

## Support

For help and support:
- Documentation: https://docs.hanzo.ai
- Discord: https://discord.gg/hanzoai
- GitHub: https://github.com/hanzoai