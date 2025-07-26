"""Hanzo AI Cluster module for local private AI.

This module integrates exo-explore for distributed AI compute,
enabling local, private, and free AI inference and training.
"""

import os
import subprocess
import asyncio
from typing import Optional, List, Dict, Any
from dataclasses import dataclass
from pathlib import Path


try:
    # Try to import exo if installed
    import exo
    from exo import ExoNode, ExoCluster
    EXO_AVAILABLE = True
except ImportError:
    EXO_AVAILABLE = False
    ExoNode = None
    ExoCluster = None


@dataclass
class ClusterConfig:
    """Configuration for a Hanzo AI cluster."""
    name: str = "hanzo-cluster"
    discovery_port: int = 5678
    model_path: str = None
    node_id: str = None
    broadcast_addresses: List[str] = None
    listen_address: str = None
    max_ram: int = None
    max_vram: int = None
    enable_mining: bool = False
    mining_address: str = None


class HanzoCluster:
    """Hanzo AI Cluster for local distributed AI compute."""
    
    def __init__(self, config: ClusterConfig = None):
        """Initialize the cluster.
        
        Args:
            config: Cluster configuration
        """
        self.config = config or ClusterConfig()
        self.node = None
        self.process = None
        self._check_exo()
    
    def _check_exo(self):
        """Check if exo is available."""
        if not EXO_AVAILABLE:
            # Try to install exo
            print("exo not found. Installing exo-explore...")
            try:
                subprocess.run(
                    ["pip", "install", "exo-explore"],
                    check=True,
                    capture_output=True
                )
                # Try importing again
                import exo
                from exo import ExoNode as _ExoNode, ExoCluster as _ExoCluster
                
                # Update module-level variables
                globals()['exo'] = exo
                globals()['ExoNode'] = _ExoNode
                globals()['ExoCluster'] = _ExoCluster
                globals()['EXO_AVAILABLE'] = True
            except Exception as e:
                print(f"Failed to install exo: {e}")
                print("Please install manually: pip install exo-explore")
    
    async def start(self):
        """Start the cluster node."""
        if not EXO_AVAILABLE:
            raise RuntimeError("exo is not available. Please install: pip install exo-explore")
        
        # Build exo command
        cmd = ["exo"]
        
        if self.config.node_id:
            cmd.extend(["--node-id", self.config.node_id])
        
        if self.config.listen_address:
            cmd.extend(["--listen-address", self.config.listen_address])
        
        if self.config.broadcast_addresses:
            for addr in self.config.broadcast_addresses:
                cmd.extend(["--broadcast-address", addr])
        
        if self.config.discovery_port:
            cmd.extend(["--discovery-port", str(self.config.discovery_port)])
        
        if self.config.model_path:
            cmd.extend(["--model-path", self.config.model_path])
        
        if self.config.max_ram:
            cmd.extend(["--max-ram", str(self.config.max_ram)])
        
        if self.config.max_vram:
            cmd.extend(["--max-vram", str(self.config.max_vram)])
        
        # Start the process
        self.process = await asyncio.create_subprocess_exec(
            *cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        
        # Log output
        asyncio.create_task(self._log_output())
        
        print(f"Started Hanzo cluster node: {' '.join(cmd)}")
    
    async def _log_output(self):
        """Log output from the exo process."""
        if not self.process:
            return
        
        async for line in self.process.stdout:
            print(f"[CLUSTER] {line.decode().strip()}")
    
    async def stop(self):
        """Stop the cluster node."""
        if self.process:
            self.process.terminate()
            await self.process.wait()
            self.process = None
            print("Stopped Hanzo cluster node")
    
    def get_api_endpoint(self) -> str:
        """Get the API endpoint for the cluster.
        
        Returns:
            API endpoint URL
        """
        # Default exo API endpoint
        return f"http://localhost:8000"
    
    async def inference(self, prompt: str, model: str = None, **kwargs) -> Dict[str, Any]:
        """Run inference on the cluster.
        
        Args:
            prompt: Input prompt
            model: Model to use (optional)
            **kwargs: Additional inference parameters
            
        Returns:
            Inference result
        """
        endpoint = self.get_api_endpoint()
        
        # This would make an API call to the exo cluster
        # For now, we'll use the standard completion endpoint
        import httpx
        
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{endpoint}/v1/completions",
                json={
                    "prompt": prompt,
                    "model": model or "llama-3.2-3b",
                    **kwargs
                }
            )
            response.raise_for_status()
            return response.json()


class HanzoMiner:
    """Hanzo Miner for distributed AI compute contribution."""
    
    def __init__(self, wallet_address: str = None, cluster_config: ClusterConfig = None):
        """Initialize the miner.
        
        Args:
            wallet_address: Wallet address for mining rewards
            cluster_config: Cluster configuration
        """
        self.wallet_address = wallet_address
        self.cluster_config = cluster_config or ClusterConfig(enable_mining=True)
        self.cluster = HanzoCluster(self.cluster_config)
    
    async def start_mining(self):
        """Start mining by contributing compute to the network."""
        if not self.wallet_address:
            raise ValueError("Wallet address required for mining")
        
        self.cluster_config.mining_address = self.wallet_address
        await self.cluster.start()
        print(f"Started mining with wallet: {self.wallet_address}")
    
    async def stop_mining(self):
        """Stop mining."""
        await self.cluster.stop()
        print("Stopped mining")
    
    def get_stats(self) -> Dict[str, Any]:
        """Get mining statistics.
        
        Returns:
            Mining statistics
        """
        # This would fetch real stats from the network
        return {
            "status": "mining" if self.cluster.process else "stopped",
            "wallet": self.wallet_address,
            "compute_contributed": "N/A",
            "rewards_earned": "N/A",
        }


# Convenience functions
async def start_local_cluster(name: str = "hanzo-local", **kwargs) -> HanzoCluster:
    """Start a local AI cluster.
    
    Args:
        name: Cluster name
        **kwargs: Additional configuration
        
    Returns:
        HanzoCluster instance
    """
    config = ClusterConfig(name=name, **kwargs)
    cluster = HanzoCluster(config)
    await cluster.start()
    return cluster


async def join_mining_network(wallet_address: str, **kwargs) -> HanzoMiner:
    """Join the Hanzo mining network.
    
    Args:
        wallet_address: Your wallet address for rewards
        **kwargs: Additional configuration
        
    Returns:
        HanzoMiner instance
    """
    miner = HanzoMiner(wallet_address=wallet_address)
    await miner.start_mining()
    return miner


__all__ = [
    # Classes
    'HanzoCluster', 'HanzoMiner', 'ClusterConfig',
    # Functions
    'start_local_cluster', 'join_mining_network',
    # Status
    'EXO_AVAILABLE',
]