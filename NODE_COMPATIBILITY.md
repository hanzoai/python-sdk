# Node Software Compatibility Analysis

## Overview
The refactored `hanzo node` command structure is compatible with the existing Hanzo ecosystem, including the desktop app and network components.

## Architecture Alignment

### 1. Desktop App Integration (~/work/hanzo/app)
The Hanzo Desktop app uses a **HanzoNodeManager** architecture that aligns with our new node terminology:

**Desktop Components:**
- `HanzoNodeManager` (Rust) - Manages local node processes
- `HanzoNodeOptions` - Configuration for node instances
- `HanzoNodeProcessHandler` - Process lifecycle management
- `OllamaProcessHandler` - Manages Ollama for local models

**Key Ports & Services:**
- API Port: 9550 (node API)
- WebSocket: 9551 (real-time communication)
- P2P: 9552 (node-to-node communication)
- HTTPS: 9553 (secure API)
- Embeddings: 11435 (Ollama service)

### 2. Network Integration (~/work/hanzo/python-sdk/pkg/hanzo-network)
The network package provides distributed compute capabilities:

**Network Components:**
- `LocalComputeNode` - Local AI inference node
- `DistributedNetwork` - Multi-node coordination
- `LocalComputeOrchestrator` - Resource management
- Model providers: HuggingFace, ONNX, Llama.cpp

**Integration Points:**
- Supports multiple model providers
- Handles resource allocation (CPU/GPU/RAM)
- Implements economic layer (ETH payments)
- Provides attestation for secure inference

### 3. Router Integration (~/work/hanzo/router)
The router acts as a proxy layer for LLM requests:

**Router Role:**
- Runs on port 4000 by default
- Routes requests to appropriate models
- Handles 100+ LLM providers
- Provides unified OpenAI-compatible API

## Compatibility Matrix

| Component | Old Term | New Term | Status |
|-----------|----------|----------|---------|
| CLI Command | `hanzo cluster` | `hanzo node` | ✅ Updated |
| Desktop App | HanzoNode | HanzoNode | ✅ Compatible |
| Network Package | Node/Worker | Node/Worker | ✅ Compatible |
| Router | N/A | Router | ✅ Separate |
| Python SDK | start_cluster() | start_node() | ✅ Updated |

## Port Allocation Strategy

```
Application Layer:
├── 3000-3999: Frontend Services
│   ├── 3000: Search UI
│   └── 3081: Chat UI
│
├── 4000-4999: Router/Proxy Layer
│   └── 4000: Hanzo Router (LLM Proxy)
│
├── 8000-8999: Local AI Services
│   └── 8000: Local Node API
│
├── 9000-9999: Infrastructure
│   ├── 9090: Prometheus
│   ├── 9550: Node API
│   ├── 9551: Node WebSocket
│   ├── 9552: Node P2P
│   └── 9553: Node HTTPS
│
└── 11000-11999: Model Services
    └── 11435: Ollama Embeddings
```

## Command Structure

### New Unified Commands:
```bash
# Node Management
hanzo node start        # Start local AI node
hanzo node stop         # Stop node
hanzo node status       # Check node status
hanzo node models       # List available models
hanzo node load <model> # Load a model

# Worker Management (sub-nodes)
hanzo node worker start # Start worker process
hanzo node worker stop  # Stop worker
hanzo node worker list  # List workers

# Router Management
hanzo router start      # Start LLM proxy
hanzo router stop       # Stop proxy
hanzo router status     # Check proxy status

# Quick Aliases
hanzo serve            # Alias for 'hanzo node start'
hanzo ask              # Quick AI query
```

## Integration Points

### 1. Desktop App ↔ Python SDK
- Desktop app spawns `hanzo-node` process
- Python SDK can connect to running node via API (port 9550)
- Shared configuration through HanzoNodeOptions

### 2. Node ↔ Router
- Node can use router for external model access
- Router can forward local requests to node
- Fallback chain: Router (4000) → Node (8000) → Cloud

### 3. Node ↔ Network
- Nodes can join distributed network
- Share compute resources across nodes
- Economic layer for resource compensation

## Migration Path

For existing users:
1. `hanzo cluster` commands automatically map to `hanzo node`
2. Configuration files remain compatible
3. API endpoints unchanged
4. Desktop app continues to work without modification

## Benefits of New Structure

1. **Clearer Terminology**: "Node" better represents a single compute unit
2. **Consistent Naming**: Aligns with desktop app's HanzoNode terminology
3. **Scalability**: Workers within nodes for parallel processing
4. **Modularity**: Clear separation between node, router, and network layers
5. **Compatibility**: Maintains backward compatibility with existing ecosystem

## Future Enhancements

1. **Auto-discovery**: Nodes can automatically find each other
2. **Load Balancing**: Router can distribute across multiple nodes
3. **Federation**: Nodes can form federated learning networks
4. **Orchestration**: Advanced scheduling across node workers
5. **Monitoring**: Unified metrics across all components

## Conclusion

The refactored node software maintains full compatibility with the existing Hanzo ecosystem while providing clearer terminology and better architectural alignment. The change from "cluster" to "node" better reflects the actual architecture where a single node can have multiple workers, rather than implying a distributed cluster.