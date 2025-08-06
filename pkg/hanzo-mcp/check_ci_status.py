#!/usr/bin/env python3
"""Check CI status for hanzo packages."""

import subprocess
import sys
from pathlib import Path

def run_command(cmd: str, cwd: Path = None) -> tuple[int, str, str]:
    """Run a command and return exit code, stdout, stderr."""
    result = subprocess.run(
        cmd,
        shell=True,
        capture_output=True,
        text=True,
        cwd=cwd
    )
    return result.returncode, result.stdout, result.stderr

def check_hanzo_network():
    """Check hanzo-network tests."""
    print("\n🔍 Checking hanzo-network...")
    network_path = Path(__file__).parent.parent / "hanzo-network"
    
    # Run tests
    code, stdout, stderr = run_command(
        "python -m pytest tests/ -v --tb=short",
        cwd=network_path
    )
    
    if code == 0:
        print("✅ hanzo-network tests passed!")
    else:
        print("❌ hanzo-network tests failed!")
        print(stderr)
    
    return code == 0

def check_hanzo_mcp():
    """Check hanzo-mcp tests."""
    print("\n🔍 Checking hanzo-mcp...")
    mcp_path = Path(__file__).parent
    
    # Run E2E test
    code, stdout, stderr = run_command(
        "python -m pytest tests/test_e2e_simple.py -v --tb=short",
        cwd=mcp_path
    )
    
    if code == 0:
        print("✅ hanzo-mcp E2E tests passed!")
    else:
        print("❌ hanzo-mcp E2E tests failed!")
        print(stderr)
    
    return code == 0

def check_imports():
    """Check that all imports work."""
    print("\n🔍 Checking imports...")
    
    try:
        # Add parent directories to path
        sys.path.insert(0, str(Path(__file__).parent.parent / "hanzo-network" / "src"))
        sys.path.insert(0, str(Path(__file__).parent / "src"))
        
        from hanzo_network import (
            create_local_agent,
            create_local_distributed_network,
            create_tool,
            check_local_llm_status
        )
        from hanzo_mcp import __version__
        
        print("✅ All imports successful!")
        return True
    except Exception as e:
        print(f"❌ Import failed: {e}")
        return False

def main():
    """Main entry point."""
    print("🚀 Hanzo Packages CI Status Check")
    print("=" * 50)
    
    all_passed = True
    
    # Check imports first
    if not check_imports():
        all_passed = False
    
    # Check hanzo-network
    if not check_hanzo_network():
        all_passed = False
    
    # Check hanzo-mcp
    if not check_hanzo_mcp():
        all_passed = False
    
    print("\n" + "=" * 50)
    if all_passed:
        print("✅ All CI checks passed!")
        return 0
    else:
        print("❌ Some CI checks failed!")
        return 1

if __name__ == "__main__":
    sys.exit(main())