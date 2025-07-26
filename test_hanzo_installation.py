#!/usr/bin/env python
"""Test script to verify hanzo package installation and functionality."""

import sys
import subprocess
import traceback


def test_import():
    """Test basic imports from hanzo package."""
    print("Testing imports...")
    try:
        import hanzo
        print(f"✓ hanzo imported successfully (version: {hanzo.__version__})")
        
        # Test router import
        try:
            from hanzo import router
            print("✓ hanzo.router imported successfully")
        except ImportError as e:
            print(f"✗ Failed to import hanzo.router: {e}")
            
        # Test core exports
        exports = ["Router", "completion", "acompletion", "embedding", "aembedding", 
                  "Agent", "Network", "Tool", "MCPServer", "Client", "AsyncClient"]
        
        for export in exports:
            if hasattr(hanzo, export):
                print(f"✓ hanzo.{export} available")
            else:
                print(f"✗ hanzo.{export} not available")
                
    except ImportError as e:
        print(f"✗ Failed to import hanzo: {e}")
        traceback.print_exc()
        return False
    return True


def test_cli_commands():
    """Test CLI commands."""
    print("\nTesting CLI commands...")
    
    commands = [
        ("hanzo", "--version"),
        ("hanzo", "--help"),
        ("hanzo-mcp", "--help"),
    ]
    
    for cmd in commands:
        try:
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=5)
            if result.returncode == 0:
                print(f"✓ {' '.join(cmd)} works")
            else:
                print(f"✗ {' '.join(cmd)} failed: {result.stderr}")
        except subprocess.TimeoutExpired:
            print(f"✗ {' '.join(cmd)} timed out")
        except FileNotFoundError:
            print(f"✗ {' '.join(cmd)} command not found")
        except Exception as e:
            print(f"✗ {' '.join(cmd)} error: {e}")


def test_router_functionality():
    """Test basic router functionality."""
    print("\nTesting router functionality...")
    
    try:
        from hanzo import router
        
        # Check if main functions exist
        if hasattr(router, 'completion'):
            print("✓ router.completion function available")
        else:
            print("✗ router.completion function not available")
            
        if hasattr(router, 'Router'):
            print("✓ router.Router class available")
        else:
            print("✗ router.Router class not available")
            
    except ImportError as e:
        print(f"✗ Could not test router functionality: {e}")


def main():
    """Run all tests."""
    print("=" * 60)
    print("Hanzo Package Installation Test")
    print("=" * 60)
    
    # Check Python version
    print(f"Python version: {sys.version}")
    print()
    
    # Run tests
    test_import()
    test_cli_commands()
    test_router_functionality()
    
    print("\n" + "=" * 60)
    print("Test complete!")
    print("=" * 60)


if __name__ == "__main__":
    main()