"""Local AI compute powered by hanzo.network.

This module provides local AI inference capabilities with support for
various models and hardware acceleration, integrated with the Hanzo network
for decentralized coordination and payments.
"""

import time
import hashlib
import asyncio
from typing import Dict, Any, List, Optional
from dataclasses import dataclass, field
from enum import Enum

# Try to import ML dependencies
try:
    import torch
    import transformers
    from transformers import AutoModelForCausalLM, AutoTokenizer
    TORCH_AVAILABLE = True
except ImportError:
    TORCH_AVAILABLE = False

try:
    import numpy as np
    NUMPY_AVAILABLE = True
except ImportError:
    NUMPY_AVAILABLE = False


class ModelProvider(Enum):
    """Supported model providers for local execution."""
    HUGGINGFACE = "huggingface"
    LLAMA_CPP = "llama_cpp"
    ONNX = "onnx"
    CUSTOM = "custom"


@dataclass
class ModelConfig:
    """Configuration for a local model."""
    
    name: str
    provider: ModelProvider
    model_path: str  # Local path or HF model ID
    device: str = "cpu"  # cpu, cuda, mps
    quantization: Optional[str] = None  # int8, int4, etc.
    max_length: int = 2048
    temperature: float = 0.7
    
    # Resource requirements
    min_ram_gb: float = 4.0
    min_vram_gb: float = 0.0  # For GPU models
    estimated_tokens_per_second: float = 10.0
    
    # Pricing
    price_per_1k_tokens: float = 0.0001  # In ETH


@dataclass
class InferenceRequest:
    """Request for local inference."""
    
    request_id: str
    prompt: str
    max_tokens: int = 256
    temperature: float = 0.7
    top_p: float = 0.9
    stop_sequences: List[str] = field(default_factory=list)
    
    # Economic parameters
    max_price_eth: float = 0.001
    requester_address: Optional[str] = None
    
    # Security
    require_attestation: bool = False
    timeout_seconds: int = 60


@dataclass
class InferenceResult:
    """Result from local inference."""
    
    request_id: str
    text: str
    tokens_generated: int
    time_seconds: float
    model_name: str
    
    # Pricing
    cost_eth: float = 0.0
    
    # Attestation (if requested)
    attestation: Optional[Dict[str, Any]] = None


class LocalComputeNode:
    """Node that provides local AI compute resources."""
    
    def __init__(
        self,
        node_id: str,
        wallet_address: Optional[str] = None,
        models: Optional[List[ModelConfig]] = None
    ):
        """Initialize local compute node.
        
        Args:
            node_id: Unique node identifier
            wallet_address: Ethereum address for payments
            models: List of available models
        """
        self.node_id = node_id
        self.wallet_address = wallet_address or f"0x{hashlib.sha256(node_id.encode()).hexdigest()[:40]}"
        self.models: Dict[str, ModelConfig] = {}
        self.loaded_models: Dict[str, Any] = {}
        
        # Add default models if none provided
        if not models:
            models = self._get_default_models()
        
        for model in models:
            self.models[model.name] = model
        
        # Performance tracking
        self.total_requests = 0
        self.total_tokens = 0
        self.total_earnings = 0.0
        
        # Resource monitoring
        self.cpu_usage = 0.0
        self.memory_usage = 0.0
        self.gpu_usage = 0.0
    
    def _get_default_models(self) -> List[ModelConfig]:
        """Get default model configurations."""
        models = []
        
        # Small model for CPU
        models.append(ModelConfig(
            name="hanzo-nano",
            provider=ModelProvider.HUGGINGFACE,
            model_path="microsoft/phi-2",  # 2.7B model
            device="cpu",
            min_ram_gb=8.0,
            estimated_tokens_per_second=20.0,
            price_per_1k_tokens=0.00001
        ))
        
        # Medium model for GPU
        if torch.cuda.is_available():
            models.append(ModelConfig(
                name="hanzo-base",
                provider=ModelProvider.HUGGINGFACE,
                model_path="mistralai/Mistral-7B-v0.1",
                device="cuda",
                min_ram_gb=16.0,
                min_vram_gb=8.0,
                estimated_tokens_per_second=50.0,
                price_per_1k_tokens=0.00005
            ))
        
        return models
    
    def list_models(self) -> List[Dict[str, Any]]:
        """List available models and their capabilities."""
        model_list = []
        
        for name, config in self.models.items():
            # Check if model can run on current hardware
            available = self._check_resources(config)
            
            model_list.append({
                "name": name,
                "provider": config.provider.value,
                "device": config.device,
                "available": available,
                "price_per_1k_tokens": config.price_per_1k_tokens,
                "estimated_tps": config.estimated_tokens_per_second,
                "min_ram_gb": config.min_ram_gb,
                "min_vram_gb": config.min_vram_gb
            })
        
        return model_list
    
    def _check_resources(self, config: ModelConfig) -> bool:
        """Check if system has resources for model."""
        # Simple check - in production would be more sophisticated
        if not TORCH_AVAILABLE:
            return False
        
        # Check RAM
        try:
            import psutil
            available_ram_gb = psutil.virtual_memory().available / (1024**3)
            if available_ram_gb < config.min_ram_gb:
                return False
        except:
            pass
        
        # Check GPU if needed
        if config.device == "cuda" and config.min_vram_gb > 0:
            if not torch.cuda.is_available():
                return False
            
            # Check VRAM
            try:
                vram_gb = torch.cuda.get_device_properties(0).total_memory / (1024**3)
                if vram_gb < config.min_vram_gb:
                    return False
            except:
                return False
        
        return True
    
    def load_model(self, model_name: str) -> bool:
        """Load a model into memory.
        
        Args:
            model_name: Name of model to load
            
        Returns:
            True if successful
        """
        if model_name in self.loaded_models:
            return True
        
        if model_name not in self.models:
            print(f"Unknown model: {model_name}")
            return False
        
        config = self.models[model_name]
        
        if not self._check_resources(config):
            print(f"Insufficient resources for {model_name}")
            return False
        
        try:
            if config.provider == ModelProvider.HUGGINGFACE:
                # Load HuggingFace model
                tokenizer = AutoTokenizer.from_pretrained(config.model_path)
                model = AutoModelForCausalLM.from_pretrained(
                    config.model_path,
                    torch_dtype=torch.float16 if config.device != "cpu" else torch.float32,
                    device_map="auto" if config.device == "cuda" else None
                )
                
                if config.device == "cuda":
                    model = model.cuda()
                
                self.loaded_models[model_name] = {
                    "model": model,
                    "tokenizer": tokenizer,
                    "config": config
                }
                
                print(f"Loaded model: {model_name}")
                return True
                
            else:
                print(f"Provider {config.provider} not implemented")
                return False
                
        except Exception as e:
            print(f"Failed to load {model_name}: {e}")
            return False
    
    async def process_request(self, request: InferenceRequest) -> InferenceResult:
        """Process an inference request.
        
        Args:
            request: Inference request
            
        Returns:
            Inference result
        """
        start_time = time.time()
        
        # Select best available model within price range
        selected_model = None
        for name, config in self.models.items():
            cost_estimate = (request.max_tokens / 1000) * config.price_per_1k_tokens
            if cost_estimate <= request.max_price_eth:
                if self._check_resources(config):
                    selected_model = name
                    break
        
        if not selected_model:
            return InferenceResult(
                request_id=request.request_id,
                text="Error: No suitable model available within price range",
                tokens_generated=0,
                time_seconds=0,
                model_name="none"
            )
        
        # Load model if needed
        if not self.load_model(selected_model):
            return InferenceResult(
                request_id=request.request_id,
                text="Error: Failed to load model",
                tokens_generated=0,
                time_seconds=0,
                model_name=selected_model
            )
        
        # Run inference
        try:
            result_text = await self._run_inference(
                selected_model,
                request.prompt,
                request.max_tokens,
                request.temperature,
                request.top_p,
                request.stop_sequences
            )
            
            # Calculate cost
            tokens_generated = len(result_text.split())  # Approximate
            cost = (tokens_generated / 1000) * self.models[selected_model].price_per_1k_tokens
            
            # Update statistics
            self.total_requests += 1
            self.total_tokens += tokens_generated
            self.total_earnings += cost
            
            # Create result
            result = InferenceResult(
                request_id=request.request_id,
                text=result_text,
                tokens_generated=tokens_generated,
                time_seconds=time.time() - start_time,
                model_name=selected_model,
                cost_eth=cost
            )
            
            # Add attestation if requested
            if request.require_attestation:
                result.attestation = self._create_attestation(request, result)
            
            return result
            
        except Exception as e:
            return InferenceResult(
                request_id=request.request_id,
                text=f"Error during inference: {str(e)}",
                tokens_generated=0,
                time_seconds=time.time() - start_time,
                model_name=selected_model
            )
    
    async def _run_inference(
        self,
        model_name: str,
        prompt: str,
        max_tokens: int,
        temperature: float,
        top_p: float,
        stop_sequences: List[str]
    ) -> str:
        """Run inference with a loaded model."""
        if not TORCH_AVAILABLE:
            # Fallback to mock inference
            await asyncio.sleep(0.1)  # Simulate processing
            return f"Mock response to: {prompt[:50]}..."
        
        model_data = self.loaded_models[model_name]
        model = model_data["model"]
        tokenizer = model_data["tokenizer"]
        config = model_data["config"]
        
        # Tokenize input
        inputs = tokenizer(prompt, return_tensors="pt")
        if config.device == "cuda":
            inputs = {k: v.cuda() for k, v in inputs.items()}
        
        # Generate
        with torch.no_grad():
            outputs = model.generate(
                **inputs,
                max_new_tokens=max_tokens,
                temperature=temperature,
                top_p=top_p,
                do_sample=True,
                pad_token_id=tokenizer.eos_token_id
            )
        
        # Decode
        response = tokenizer.decode(outputs[0], skip_special_tokens=True)
        
        # Remove prompt from response
        if response.startswith(prompt):
            response = response[len(prompt):].strip()
        
        return response
    
    def _create_attestation(
        self,
        request: InferenceRequest,
        result: InferenceResult
    ) -> Dict[str, Any]:
        """Create attestation for inference result."""
        # In production, this would use TEE attestation
        attestation_data = {
            "node_id": self.node_id,
            "request_id": request.request_id,
            "model_name": result.model_name,
            "prompt_hash": hashlib.sha256(request.prompt.encode()).hexdigest(),
            "result_hash": hashlib.sha256(result.text.encode()).hexdigest(),
            "timestamp": time.time()
        }
        
        # Create signature (mock)
        signature_data = json.dumps(attestation_data, sort_keys=True)
        signature = hashlib.sha256(signature_data.encode()).hexdigest()
        
        return {
            "data": attestation_data,
            "signature": signature,
            "provider": "mock_tee"
        }
    
    def get_stats(self) -> Dict[str, Any]:
        """Get node statistics."""
        return {
            "node_id": self.node_id,
            "wallet_address": self.wallet_address,
            "models_available": len(self.models),
            "models_loaded": len(self.loaded_models),
            "total_requests": self.total_requests,
            "total_tokens": self.total_tokens,
            "total_earnings_eth": self.total_earnings,
            "avg_tokens_per_request": self.total_tokens / max(1, self.total_requests),
            "resource_usage": {
                "cpu_percent": self.cpu_usage,
                "memory_percent": self.memory_usage,
                "gpu_percent": self.gpu_usage
            }
        }


class LocalComputeOrchestrator:
    """Orchestrates multiple local compute nodes."""
    
    def __init__(self):
        """Initialize orchestrator."""
        self.nodes: Dict[str, LocalComputeNode] = {}
        self.pending_requests: List[InferenceRequest] = []
        self.completed_requests: Dict[str, InferenceResult] = {}
    
    def register_node(self, node: LocalComputeNode):
        """Register a compute node."""
        self.nodes[node.node_id] = node
        print(f"Registered node: {node.node_id}")
    
    async def submit_request(self, request: InferenceRequest) -> str:
        """Submit an inference request.
        
        Args:
            request: Inference request
            
        Returns:
            Request ID for tracking
        """
        # Find suitable node
        best_node = None
        best_price = float('inf')
        
        for node in self.nodes.values():
            for model in node.list_models():
                if model["available"]:
                    estimated_cost = (request.max_tokens / 1000) * model["price_per_1k_tokens"]
                    if estimated_cost <= request.max_price_eth and estimated_cost < best_price:
                        best_node = node
                        best_price = estimated_cost
        
        if not best_node:
            # Queue request
            self.pending_requests.append(request)
            return f"Request {request.request_id} queued (no available nodes)"
        
        # Process immediately
        result = await best_node.process_request(request)
        self.completed_requests[request.request_id] = result
        
        return f"Request {request.request_id} completed by {best_node.node_id}"
    
    def get_result(self, request_id: str) -> Optional[InferenceResult]:
        """Get result for a request."""
        return self.completed_requests.get(request_id)
    
    def get_network_stats(self) -> Dict[str, Any]:
        """Get network-wide statistics."""
        total_models = sum(len(node.models) for node in self.nodes.values())
        total_requests = sum(node.total_requests for node in self.nodes.values())
        total_earnings = sum(node.total_earnings for node in self.nodes.values())
        
        return {
            "nodes": len(self.nodes),
            "total_models": total_models,
            "pending_requests": len(self.pending_requests),
            "completed_requests": len(self.completed_requests),
            "total_requests_processed": total_requests,
            "total_earnings_eth": total_earnings,
            "nodes_detail": {
                node_id: node.get_stats()
                for node_id, node in self.nodes.items()
            }
        }


# Global orchestrator instance
orchestrator = LocalComputeOrchestrator()


# Example usage function
async def demo_local_compute():
    """Demonstrate local compute capabilities."""
    # Create a compute node
    node1 = LocalComputeNode(
        node_id="node_001",
        wallet_address="0x1234567890123456789012345678901234567890"
    )
    
    # Register with orchestrator
    orchestrator.register_node(node1)
    
    # List available models
    print("\nAvailable models:")
    for model in node1.list_models():
        print(f"  - {model['name']}: {model['device']}, ${model['price_per_1k_tokens']}/1k tokens")
    
    # Create inference request
    request = InferenceRequest(
        request_id="req_001",
        prompt="What is the capital of France?",
        max_tokens=50,
        max_price_eth=0.001
    )
    
    # Submit request
    status = await orchestrator.submit_request(request)
    print(f"\nRequest status: {status}")
    
    # Get result
    result = orchestrator.get_result("req_001")
    if result:
        print("\nResult:")
        print(f"  Model: {result.model_name}")
        print(f"  Response: {result.text}")
        print(f"  Cost: {result.cost_eth:.6f} ETH")
        print(f"  Time: {result.time_seconds:.2f}s")
    
    # Show stats
    print("\nNetwork stats:")
    stats = orchestrator.get_network_stats()
    print(f"  Nodes: {stats['nodes']}")
    print(f"  Total models: {stats['total_models']}")
    print(f"  Total earnings: {stats['total_earnings_eth']:.6f} ETH")


if __name__ == "__main__":
    # Run demo
    asyncio.run(demo_local_compute())