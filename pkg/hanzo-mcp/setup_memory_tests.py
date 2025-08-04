#!/usr/bin/env python
"""Setup script to enable memory tests by installing minimal dependencies."""

import subprocess
import sys
import os

def main():
    """Install minimal dependencies for memory tests."""
    print("Setting up memory tests...")
    
    # Add hanzo-memory to Python path
    memory_path = os.path.abspath("../hanzo-memory/src")
    if memory_path not in sys.path:
        sys.path.insert(0, memory_path)
    
    # Install minimal required dependencies
    required_deps = [
        "polars>=1.15.0",
        "lancedb>=0.8.0",
        "chromadb>=0.5.0",
        "fastembed>=0.4.0",
        "sentence-transformers>=5.0.0",
    ]
    
    print("\nInstalling minimal dependencies for memory tests...")
    for dep in required_deps:
        print(f"Installing {dep}...")
        try:
            subprocess.run([sys.executable, "-m", "pip", "install", dep, "--quiet"], check=True)
        except subprocess.CalledProcessError as e:
            print(f"Warning: Failed to install {dep}: {e}")
    
    # Test import
    print("\nTesting hanzo_memory import...")
    try:
        sys.path.insert(0, memory_path)
        import hanzo_memory
        print(f"✓ Successfully imported hanzo_memory from {memory_path}")
        print(f"  Version: {getattr(hanzo_memory, '__version__', 'unknown')}")
    except ImportError as e:
        print(f"✗ Failed to import hanzo_memory: {e}")
        return 1
    
    print("\nMemory tests setup complete!")
    print("\nTo run memory tests:")
    print("  export PYTHONPATH=../hanzo-memory/src:$PYTHONPATH")
    print("  python -m pytest tests/test_memory*.py -v")
    
    return 0

if __name__ == "__main__":
    sys.exit(main())