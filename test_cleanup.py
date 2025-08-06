#!/usr/bin/env python3
"""Test script to verify package cleanup and structure."""

import subprocess
import sys
from pathlib import Path

def run_command(cmd, cwd=None):
    """Run a command and return success status."""
    try:
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True, cwd=cwd)
        return result.returncode == 0, result.stdout, result.stderr
    except Exception as e:
        return False, "", str(e)

def test_package_structure():
    """Test the cleaned-up package structure."""
    base_path = Path("/Users/z/work/hanzo/python-sdk")
    pkg_path = base_path / "pkg"
    
    print("=" * 60)
    print("HANZO PYTHON SDK - PACKAGE CLEANUP VERIFICATION")
    print("=" * 60)
    
    # Expected packages after cleanup
    expected_packages = [
        "hanzo",        # Main package (renamed from hanzo-wrapper)
        "hanzo-aci",    # Agent-Computer Interface
        "hanzo-agents", # Agent frameworks
        "hanzo-mcp",    # Model Context Protocol
        "hanzo-memory", # Memory systems
        "hanzo-network",# Network infrastructure
        "hanzo-repl",   # REPL interface
        "hanzoai",      # SDK client library
    ]
    
    # Removed packages (should not exist)
    removed_packages = [
        "hanzo-cli",        # Merged into hanzo
        "hanzo-mcp-client", # Removed - using official client
        "hanzo-a2a",        # Empty - removed
        "hanzo-cluster",    # Empty - removed
        "hanzo-miner",      # Empty - removed
        "hanzo-tools",      # Empty - removed
    ]
    
    print("\n1. PACKAGE STRUCTURE CHECK")
    print("-" * 40)
    
    # Check expected packages exist
    print("\n✅ Active Packages (should exist):")
    for pkg in expected_packages:
        pkg_dir = pkg_path / pkg
        if pkg_dir.exists():
            # Check for pyproject.toml
            pyproject = pkg_dir / "pyproject.toml"
            has_pyproject = "✓" if pyproject.exists() else "✗"
            print(f"   ✓ {pkg:20} [pyproject.toml: {has_pyproject}]")
        else:
            print(f"   ✗ {pkg:20} [MISSING]")
    
    print("\n🗑️  Removed Packages (should NOT exist):")
    for pkg in removed_packages:
        pkg_dir = pkg_path / pkg
        if not pkg_dir.exists():
            print(f"   ✓ {pkg:20} [Successfully removed]")
        else:
            print(f"   ✗ {pkg:20} [STILL EXISTS - needs removal]")
    
    print("\n2. TEST EXECUTION")
    print("-" * 40)
    
    # Run tests for each package with tests
    test_results = {}
    packages_with_tests = ["hanzo-mcp", "hanzo-aci", "hanzo-network", "hanzo-agents", "hanzo-memory"]
    
    for pkg in packages_with_tests:
        pkg_dir = pkg_path / pkg
        if pkg_dir.exists():
            print(f"\nTesting {pkg}...")
            success, stdout, stderr = run_command(
                "python -m pytest tests/ -v --tb=short -x 2>&1 | head -20",
                cwd=str(pkg_dir)
            )
            if "passed" in stdout or "PASSED" in stdout:
                test_results[pkg] = "PASSED"
                print(f"   ✓ Tests found and running")
            elif "no tests ran" in stdout.lower() or "not found" in stderr.lower():
                test_results[pkg] = "NO TESTS"
                print(f"   ⚠ No tests found")
            else:
                test_results[pkg] = "FAILED"
                print(f"   ✗ Tests failed or error")
    
    print("\n3. PACKAGE DEPENDENCIES")
    print("-" * 40)
    
    # Check main hanzo package dependencies
    hanzo_pyproject = pkg_path / "hanzo" / "pyproject.toml"
    if hanzo_pyproject.exists():
        with open(hanzo_pyproject) as f:
            content = f.read()
            if "hanzo-cli" not in content and "hanzo-mcp-client" not in content:
                print("✓ Main hanzo package cleaned of removed dependencies")
            else:
                print("✗ Main hanzo package still has references to removed packages")
    
    print("\n4. SUMMARY")
    print("-" * 40)
    
    total_packages = len([p for p in expected_packages if (pkg_path / p).exists()])
    print(f"Total active packages: {total_packages}/{len(expected_packages)}")
    
    removed_count = len([p for p in removed_packages if not (pkg_path / p).exists()])
    print(f"Successfully removed: {removed_count}/{len(removed_packages)}")
    
    if test_results:
        passed = len([v for v in test_results.values() if v == "PASSED"])
        print(f"Packages with passing tests: {passed}/{len(test_results)}")
    
    print("\n" + "=" * 60)
    print("CLEANUP VERIFICATION COMPLETE")
    print("=" * 60)
    
    # Return success if all expected packages exist and all removed packages are gone
    all_expected_exist = all((pkg_path / p).exists() for p in expected_packages)
    all_removed_gone = all(not (pkg_path / p).exists() for p in removed_packages)
    
    if all_expected_exist and all_removed_gone:
        print("\n✅ Package cleanup successful!")
        return 0
    else:
        print("\n⚠️  Some issues remain - review output above")
        return 1

if __name__ == "__main__":
    sys.exit(test_package_structure())