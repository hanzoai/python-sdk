"""Compute node detection and management for distributed processing."""

import os
import platform
import subprocess
from typing import Any, Dict, List


class ComputeNodeDetector:
    """Detect available compute nodes (GPUs, WebGPU, CPUs) for distributed work."""

    @staticmethod
    def detect_local_gpus() -> List[Dict[str, Any]]:
        """Detect local GPU devices."""
        gpus = []

        # Try NVIDIA GPUs
        try:
            result = subprocess.run(
                [
                    "nvidia-smi",
                    "--query-gpu=name,memory.total",
                    "--format=csv,noheader",
                ],
                capture_output=True,
                text=True,
                timeout=2,
            )
            if result.returncode == 0:
                for line in result.stdout.strip().split("\n"):
                    if line:
                        name, memory = line.split(", ")
                        gpus.append(
                            {
                                "type": "cuda",
                                "name": name,
                                "memory": memory,
                                "id": f"cuda:{len(gpus)}",
                            }
                        )
        except (FileNotFoundError, subprocess.TimeoutExpired):
            pass

        # Try Metal GPUs (macOS)
        if platform.system() == "Darwin":
            try:
                # Check for Metal support
                result = subprocess.run(
                    ["system_profiler", "SPDisplaysDataType"],
                    capture_output=True,
                    text=True,
                    timeout=2,
                )
                if result.returncode == 0 and "Metal" in result.stdout:
                    # Parse GPU info from system_profiler
                    lines = result.stdout.split("\n")
                    for i, line in enumerate(lines):
                        if "Chipset Model:" in line:
                            gpu_name = line.split(":")[1].strip()
                            gpus.append(
                                {
                                    "type": "metal",
                                    "name": gpu_name,
                                    "memory": "Shared",
                                    "id": f"metal:{len(gpus)}",
                                }
                            )
            except (FileNotFoundError, subprocess.TimeoutExpired):
                pass

        return gpus

    @staticmethod
    def detect_webgpu_nodes() -> List[Dict[str, Any]]:
        """Detect connected WebGPU nodes (from browsers)."""
        webgpu_nodes = []

        # Check for WebGPU connections (would need actual WebSocket/server to track)
        # For now, check if a WebGPU server is running
        webgpu_port = os.environ.get("HANZO_WEBGPU_PORT", "8765")
        try:
            import socket

            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            result = sock.connect_ex(("localhost", int(webgpu_port)))
            sock.close()
            if result == 0:
                webgpu_nodes.append(
                    {
                        "type": "webgpu",
                        "name": "Chrome WebGPU",
                        "memory": "Browser",
                        "id": "webgpu:0",
                    }
                )
        except Exception:
            pass

        return webgpu_nodes

    @staticmethod
    def detect_cpu_nodes() -> List[Dict[str, Any]]:
        """Detect CPU compute nodes."""
        import multiprocessing

        return [
            {
                "type": "cpu",
                "name": f"{platform.processor() or 'CPU'}",
                "cores": multiprocessing.cpu_count(),
                "id": "cpu:0",
            }
        ]

    @classmethod
    def get_all_nodes(cls) -> List[Dict[str, Any]]:
        """Get all available compute nodes."""
        nodes = []

        # Detect GPUs
        gpus = cls.detect_local_gpus()
        nodes.extend(gpus)

        # Detect WebGPU connections
        webgpu = cls.detect_webgpu_nodes()
        nodes.extend(webgpu)

        # If no GPUs/WebGPU, add CPU as compute node
        if not nodes:
            nodes.extend(cls.detect_cpu_nodes())

        return nodes

    @classmethod
    def get_node_count(cls) -> int:
        """Get total number of available compute nodes."""
        return len(cls.get_all_nodes())

    @classmethod
    def get_node_summary(cls) -> str:
        """Get a summary string of available nodes."""
        nodes = cls.get_all_nodes()
        if not nodes:
            return "No compute nodes available"

        count = len(nodes)
        node_word = "node" if count == 1 else "nodes"

        # Group by type
        types = {}
        for node in nodes:
            node_type = node["type"]
            if node_type not in types:
                types[node_type] = 0
            types[node_type] += 1

        # Build summary
        parts = []
        for node_type, type_count in types.items():
            if node_type == "cuda":
                parts.append(f"{type_count} CUDA GPU{'s' if type_count > 1 else ''}")
            elif node_type == "metal":
                parts.append(f"{type_count} Metal GPU{'s' if type_count > 1 else ''}")
            elif node_type == "webgpu":
                parts.append(f"{type_count} WebGPU")
            elif node_type == "cpu":
                parts.append(f"{type_count} CPU")

        type_str = ", ".join(parts)
        return f"{count} {node_word} available ({type_str})"


def print_node_status():
    """Print current node status."""
    detector = ComputeNodeDetector()
    nodes = detector.get_all_nodes()

    print(f"\n🖥️  Compute Nodes: {len(nodes)}")
    for node in nodes:
        if node["type"] in ["cuda", "metal"]:
            print(f"  • {node['id']}: {node['name']} ({node['memory']})")
        elif node["type"] == "webgpu":
            print(f"  • {node['id']}: {node['name']}")
        elif node["type"] == "cpu":
            print(f"  • {node['id']}: {node['name']} ({node['cores']} cores)")
    print()


if __name__ == "__main__":
    # Test the detector
    print_node_status()
    print(ComputeNodeDetector.get_node_summary())
