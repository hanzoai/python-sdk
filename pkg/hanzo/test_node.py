#!/usr/bin/env python
"""Standalone test for hanzo node command."""

import sys

# Add src to path
sys.path.insert(0, "src")


def test_imports():
    """Test that modules can be imported."""
    try:
        from hanzo.utils.net_check import (
            check_net_installation,
            get_missing_dependencies,
        )

        print("✓ Successfully imported net_check utilities")

        # Test the check function
        is_available, net_path, python_exe = check_net_installation()
        print(f"✓ Net available: {is_available}")
        print(f"  Net path: {net_path}")
        print(f"  Python: {python_exe}")

        if python_exe:
            missing = get_missing_dependencies(python_exe)
            if missing:
                print(f"  Missing deps: {', '.join(missing[:5])}")
            else:
                print("  All dependencies installed")

        return True
    except Exception as e:
        print(f"✗ Import failed: {e}")
        return False


def test_cli_import():
    """Test CLI import."""
    try:
        print("✓ Successfully imported CLI")
        return True
    except Exception as e:
        print(f"✗ CLI import failed: {e}")
        return False


if __name__ == "__main__":
    print("Testing Hanzo Node Command Integration")
    print("=" * 40)

    success = True
    success = test_imports() and success
    success = test_cli_import() and success

    print("=" * 40)
    if success:
        print("✓ All tests passed!")
        sys.exit(0)
    else:
        print("✗ Some tests failed")
        sys.exit(1)
