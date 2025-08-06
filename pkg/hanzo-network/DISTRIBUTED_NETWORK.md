# Hanzo Distributed Network

This document describes the distributed networking capabilities integrated from hanzo/net into hanzo-network.

## Overview

The distributed network extends the base `Network` class with:
- Automatic peer discovery via UDP broadcast
- Distributed agent execution across nodes
- Cross-node state synchronization
- Load balancing across nodes
- Device capability detection and reporting

## Key Components

### 1. UDP Discovery (`udp_discovery.py`)
- Broadcasts node presence on the local network
- Discovers other nodes automatically
- Maintains peer health checks
- Supports network interface prioritization

### 2. gRPC Server (`grpc_server.py`)
- Handles peer-to-peer communication
- Executes remote agent requests
- Manages distributed state sync
- Currently a simplified implementation for testing

### 3. Device Capabilities (`device_capabilities.py`)
- Detects hardware (CPU, GPU, memory)
- Reports compute capabilities (TFLOPS)
- Supports macOS, Linux, and Windows
- Used for intelligent agent placement

### 4. Distributed Network (`distributed_network.py`)
- Extends base Network with distributed features
- Manages peer discovery and communication
- Routes agent execution to appropriate nodes
- Synchronizes state across the network

## Usage

### Basic Example

```python
from hanzo_network import create_distributed_network, create_agent, create_tool

# Create agents
agent = create_agent(
    name="my_agent",
    description="Example agent",
    tools=[...]
)

# Create distributed network
network = create_distributed_network(
    agents=[agent],
    name="my-network",
    node_id="node-1",
    listen_port=5678,
    broadcast_port=5678
)

# Start network
await network.start(wait_for_peers=0)

# Check status
status = network.get_network_status()
print(f"Peers: {status['peer_count']}")

# Execute agent (locally or remotely)
result = await network.run("Do something", initial_agent=agent)
```

### Multi-Node Setup

Run on different machines or terminals:

**Node 1:**
```python
network1 = create_distributed_network(
    agents=[weather_agent],
    node_id="node-1",
    listen_port=5681,
    broadcast_port=5678  # Same broadcast port
)
await network1.start()
```

**Node 2:**
```python
network2 = create_distributed_network(
    agents=[math_agent],
    node_id="node-2", 
    listen_port=5682,
    broadcast_port=5678  # Same broadcast port
)
await network2.start()
```

The nodes will automatically discover each other and share agent capabilities.

## Architecture

```
┌─────────────────┐     UDP Broadcast      ┌─────────────────┐
│                 │ ◄──────────────────────► │                 │
│   Node 1        │                         │   Node 2        │
│                 │      gRPC Requests      │                 │
│ - Weather Agent │ ◄──────────────────────► │ - Math Agent    │
│ - Discovery     │                         │ - Discovery     │
│ - gRPC Server   │                         │ - gRPC Server   │
└─────────────────┘                         └─────────────────┘
        │                                             │
        └─────────────────┬───────────────────────────┘
                          │
                    State Sync &
                    Agent Registry
```

## Testing

All distributed network tests are passing:

```bash
python -m pytest tests/test_distributed_network.py -v
```

Tests cover:
- Network creation and configuration
- Start/stop operations
- Local agent execution
- Peer discovery simulation
- Router integration

## Future Enhancements

The current implementation is a foundation. Future work includes:

1. **Real gRPC Implementation**: Replace simplified gRPC with full protocol buffers
2. **NATS Integration**: Add NATS as an alternative discovery mechanism
3. **Security**: Add authentication and encryption for peer communication
4. **Advanced Routing**: Implement load balancing and fault tolerance
5. **State Replication**: Full state synchronization across nodes
6. **GPU Support**: Leverage GPU detection for ML workload placement

## Integration with hanzo-mcp

The distributed network can be used by hanzo-mcp to create agent networks that span multiple machines, enabling:
- Distributed AI workloads
- Peer-to-peer agent collaboration
- Local compute resource utilization
- Reduced API costs through local model execution