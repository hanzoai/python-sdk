"""Utilities for checking hanzo/net availability and dependencies."""

import sys
import subprocess
from typing import Tuple, Optional
from pathlib import Path


def check_net_installation() -> Tuple[bool, Optional[str], Optional[str]]:
    """Check if hanzo/net is available and properly configured.

    Returns:
        Tuple of (is_available, net_path, python_exe)
    """
    # First try to import as PyPI package (hanzo-net)
    try:
        import net

        return True, None, sys.executable
    except ImportError:
        pass

    # For development: check for hanzo/net in standard location
    net_path = Path.home() / "work" / "hanzo" / "net"
    if not net_path.exists():
        net_path = Path("/Users/z/work/hanzo/net")

    if not net_path.exists():
        return False, None, None

    # Check for venv
    venv_python = net_path / ".venv" / "bin" / "python"
    if venv_python.exists():
        # Check if venv has required packages
        result = subprocess.run(
            [str(venv_python), "-c", "import net, scapy, mlx, transformers"],
            capture_output=True,
            text=True,
        )
        if result.returncode == 0:
            return True, str(net_path), str(venv_python)
        else:
            # Venv exists but missing dependencies
            return False, str(net_path), str(venv_python)

    # No venv, check system Python
    result = subprocess.run(
        [sys.executable, "-c", "import scapy"], capture_output=True, text=True
    )

    if result.returncode == 0:
        return True, str(net_path), sys.executable
    else:
        return False, str(net_path), None


def install_net_dependencies(net_path: str, python_exe: str = None) -> bool:
    """Install hanzo/net dependencies.

    Args:
        net_path: Path to hanzo/net directory
        python_exe: Python executable to use (optional)

    Returns:
        True if installation successful
    """
    if python_exe is None:
        python_exe = sys.executable

    # Install dependencies
    result = subprocess.run(
        [python_exe, "-m", "pip", "install", "-e", net_path],
        capture_output=True,
        text=True,
    )

    return result.returncode == 0


def get_missing_dependencies(python_exe: str = None) -> list:
    """Check which dependencies are missing for hanzo/net.

    Args:
        python_exe: Python executable to check (default: sys.executable)

    Returns:
        List of missing package names
    """
    if python_exe is None:
        python_exe = sys.executable

    required_packages = [
        "scapy",
        "mlx",
        "mlx_lm",
        "transformers",
        "tinygrad",
        "aiohttp",
        "grpcio",
        "pydantic",
        "rich",
        "tqdm",
    ]

    missing = []
    for package in required_packages:
        result = subprocess.run(
            [python_exe, "-c", f"import {package}"], capture_output=True, text=True
        )
        if result.returncode != 0:
            missing.append(package)

    return missing
