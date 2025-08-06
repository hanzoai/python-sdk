"""Helper functions for distributed Hanzo networks."""

import os
import asyncio
import socket
import random
import platform
import psutil
import subprocess
from typing import Tuple, List
from concurrent.futures import ThreadPoolExecutor

DEBUG = int(os.getenv("DEBUG", default="0"))
DEBUG_DISCOVERY = int(os.getenv("DEBUG_DISCOVERY", default="0"))
VERSION = "0.1.0"

# Single shared thread pool for subprocess operations
subprocess_pool = ThreadPoolExecutor(max_workers=4, thread_name_prefix="subprocess_worker")


def get_system_info():
    """Get basic system information."""
    if psutil.MACOS:
        if platform.machine() == "arm64":
            return "Apple Silicon Mac"
        if platform.machine() in ["x86_64", "i386"]:
            return "Intel Mac"
        return "Unknown Mac architecture"
    if psutil.LINUX:
        return "Linux"
    return "Non-Mac, non-Linux system"


def find_available_port(host: str = "", min_port: int = 49152, max_port: int = 65535) -> int:
    """Find an available port in the specified range."""
    for _ in range(100):  # Try 100 times
        port = random.randint(min_port, max_port)
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.bind((host, port))
                return port
        except socket.error:
            continue
    raise RuntimeError("No available ports in the specified range")


def get_all_ip_addresses_and_interfaces() -> List[Tuple[str, str]]:
    """Get all IP addresses and their interface names."""
    ip_addresses = []
    
    try:
        # Get network interfaces using psutil
        interfaces = psutil.net_if_addrs()
        
        for interface_name, addrs in interfaces.items():
            for addr in addrs:
                # Only IPv4 addresses
                if addr.family == socket.AF_INET:
                    ip = addr.address
                    # Skip loopback and invalid addresses
                    if not ip.startswith("127.") and not ip.startswith("0."):
                        ip_addresses.append((ip, interface_name))
    except Exception as e:
        if DEBUG >= 1:
            print(f"Failed to get IP addresses: {e}")
    
    if not ip_addresses:
        # Fallback to localhost
        return [("127.0.0.1", "lo")]
    
    return list(set(ip_addresses))


async def get_interface_priority_and_type(ifname: str) -> Tuple[int, str]:
    """Get interface priority and type based on name patterns."""
    # Loopback interface
    if ifname.startswith('lo'):
        return (6, "Loopback")
    
    # Container/virtual interfaces
    if (ifname.startswith(('docker', 'br-', 'veth', 'cni', 'flannel', 'calico', 'weave')) or 
        'bridge' in ifname):
        return (7, "Container Virtual")
    
    # Thunderbolt
    if ifname.startswith(('tb', 'nx', 'ten')):
        return (5, "Thunderbolt")
    
    # Ethernet
    if ifname.startswith(('eth', 'en')):
        return (4, "Ethernet")
    
    # WiFi
    if ifname.startswith(('wlan', 'wifi', 'wl')):
        return (3, "WiFi")
    
    # Virtual interfaces (VPNs, tunnels)
    if ifname.startswith(('tun', 'tap', 'vtun', 'utun', 'gif', 'stf')):
        return (1, "External Virtual")
    
    # Other
    return (2, "Other")


async def get_mac_system_info() -> Tuple[str, str, int]:
    """Get Mac system information using system_profiler."""
    try:
        output = await asyncio.get_running_loop().run_in_executor(
            subprocess_pool,
            lambda: subprocess.check_output(["system_profiler", "SPHardwareDataType"]).decode("utf-8")
        )
        
        model_line = next((line for line in output.split("\n") if "Model Name" in line), None)
        model_id = model_line.split(": ")[1] if model_line else "Unknown Model"
        
        chip_line = next((line for line in output.split("\n") if "Chip" in line), None)
        chip_id = chip_line.split(": ")[1] if chip_line else "Unknown Chip"
        
        memory_line = next((line for line in output.split("\n") if "Memory" in line), None)
        memory_str = memory_line.split(": ")[1] if memory_line else "Unknown Memory"
        memory_units = memory_str.split()
        memory_value = int(memory_units[0])
        memory = memory_value * 1024 if memory_units[1] == "GB" else memory_value
        
        return model_id, chip_id, memory
    except Exception as e:
        if DEBUG >= 2:
            print(f"Error getting Mac system info: {e}")
        return "Unknown Model", "Unknown Chip", 0