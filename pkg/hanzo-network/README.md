# Hanzo Network

[![PyPI](https://img.shields.io/pypi/v/hanzo-network.svg)](https://pypi.org/project/hanzo-network/)
[![Python Version](https://img.shields.io/pypi/pyversions/hanzo-network.svg)](https://pypi.org/project/hanzo-network/)

Distributed AI compute and network orchestration for Hanzo AI.

## Installation

```bash
pip install hanzo-network
```

## Features

- **Local Compute Nodes**: Run AI models locally
- **Distributed Networks**: Coordinate multiple nodes
- **Resource Management**: CPU/GPU allocation
- **Model Providers**: HuggingFace, ONNX, Llama.cpp
- **Economic Layer**: ETH-based payments
- **Attestation**: Secure inference verification

## Quick Start

### Local Compute Node

```python
from hanzo_network import LocalComputeNode, InferenceRequest

# Create compute node
node = LocalComputeNode(
    node_id="node-001",
    wallet_address="0x..."
)

# List available models
models = node.list_models()
print(f"Available models: {models}")

# Load model
node.load_model("hanzo-nano")

# Process inference request
request = InferenceRequest(
    request_id="req-001",
    prompt="What is the capital of France?",
    max_tokens=50,
    max_price_eth=0.001
)

result = await node.process_request(request)
print(f"Response: {result.text}")
print(f"Cost: {result.cost_eth} ETH")
```

### Distributed Network

```python
from hanzo_network import (
    DistributedNetwork,
    LocalComputeNode
)

# Create network
network = DistributedNetwork()

# Add compute nodes
node1 = LocalComputeNode(node_id="node-001")
node2 = LocalComputeNode(node_id="node-002")

network.register_node(node1)
network.register_node(node2)

# Submit request (auto-routes to best node)
request_id = await network.submit_request(
    InferenceRequest(
        prompt="Explain quantum computing",
        max_tokens=200
    )
)

# Get result
result = network.get_result(request_id)
```

### Model Configuration

```python
from hanzo_network import ModelConfig, ModelProvider

# Configure custom model
config = ModelConfig(
    name="my-model",
    provider=ModelProvider.HUGGINGFACE,
    model_path="microsoft/phi-2",
    device="cuda",
    quantization="int8",
    min_ram_gb=8.0,
    min_vram_gb=4.0,
    price_per_1k_tokens=0.0001
)

# Add to node
node = LocalComputeNode(node_id="node-001")
node.models["my-model"] = config
```

## Advanced Features

### Resource Monitoring

```python
from hanzo_network import ResourceMonitor

monitor = ResourceMonitor()

# Check system resources
resources = monitor.get_resources()
print(f"CPU: {resources['cpu_percent']}%")
print(f"RAM: {resources['ram_gb']} GB")
print(f"GPU: {resources['gpu_name']}")
print(f"VRAM: {resources['vram_gb']} GB")

# Check if model can run
can_run = monitor.check_model_fit(model_config)
```

### Network Discovery

```python
from hanzo_network import NetworkDiscovery

# Discover nodes on network
discovery = NetworkDiscovery()
nodes = await discovery.find_nodes(
    min_models=1,
    max_price_eth=0.001,
    required_models=["llama2:7b"]
)

for node in nodes:
    print(f"Found: {node.node_id} at {node.address}")
```

### Attestation

```python
from hanzo_network import AttestationService

# Enable attestation for secure inference
attestation = AttestationService()

request = InferenceRequest(
    prompt="Sensitive query",
    require_attestation=True
)

result = await node.process_request(request)

# Verify attestation
if result.attestation:
    valid = attestation.verify(
        result.attestation,
        request,
        result
    )
    print(f"Attestation valid: {valid}")
```

### Economic Layer

```python
from hanzo_network import PaymentChannel

# Setup payment channel
channel = PaymentChannel(
    provider_address="0x...",
    consumer_address="0x...",
    deposit_eth=0.1
)

# Make payment for inference
payment = await channel.pay(
    amount_eth=0.0001,
    request_id="req-001"
)

# Close channel
await channel.close()
```

## Orchestration

### Local Orchestrator

```python
from hanzo_network import LocalComputeOrchestrator

orchestrator = LocalComputeOrchestrator()

# Register multiple nodes
for i in range(5):
    node = LocalComputeNode(node_id=f"node-{i:03d}")
    orchestrator.register_node(node)

# Submit batch requests
requests = [
    InferenceRequest(prompt=f"Question {i}")
    for i in range(10)
]

results = await orchestrator.process_batch(requests)
```

### Load Balancing

```python
from hanzo_network import LoadBalancer

balancer = LoadBalancer(
    strategy="least_loaded",  # least_loaded, round_robin, weighted
    health_check_interval=30
)

# Add nodes
balancer.add_node(node1, weight=1.0)
balancer.add_node(node2, weight=2.0)

# Route request
selected_node = balancer.select_node(request)
```

## Configuration

### Environment Variables

```bash
# Network settings
HANZO_NETWORK_ID=mainnet
HANZO_NODE_ID=node-001

# Wallet
HANZO_WALLET_ADDRESS=0x...
HANZO_PRIVATE_KEY=...

# Model settings
HANZO_MODEL_PATH=/models
HANZO_DEFAULT_DEVICE=cuda

# Pricing
HANZO_BASE_PRICE_ETH=0.0001
HANZO_PRICE_MULTIPLIER=1.0
```

### Configuration File

```yaml
network:
  id: mainnet
  discovery:
    enabled: true
    port: 9552
    
node:
  id: node-001
  wallet: "0x..."
  
models:
  - name: hanzo-nano
    provider: huggingface
    path: microsoft/phi-2
    device: cuda
    price: 0.0001
    
  - name: hanzo-base
    provider: llama_cpp
    path: /models/llama2-7b.gguf
    device: cpu
    price: 0.00005
    
resources:
  max_concurrent: 3
  max_memory_gb: 16
  reserved_memory_gb: 4
```

## Performance

### Benchmarks

| Model | Device | Tokens/sec | Memory |
|-------|--------|-----------|--------|
| Phi-2 | CPU | 20 | 4GB |
| Phi-2 | GPU | 50 | 3GB |
| Llama2-7B | CPU | 10 | 8GB |
| Llama2-7B | GPU | 40 | 6GB |

### Optimization

- Use quantization for larger models
- Enable GPU acceleration when available
- Implement request batching
- Use model caching
- Configure appropriate timeouts

## Development

### Setup

```bash
cd pkg/hanzo-network
uv sync --all-extras
```

### Testing

```bash
# Run tests
pytest tests/

# Integration tests
pytest tests/ -m integration

# With coverage
pytest tests/ --cov=hanzo_network
```

### Building

```bash
uv build
```

## License

Apache License 2.0