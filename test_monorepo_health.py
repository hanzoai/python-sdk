#!/usr/bin/env python3
"""Test script to verify all packages in the monorepo are healthy."""

import subprocess
import sys
from pathlib import Path
from typing import Dict, List, Tuple

# Disable DataDog tracing
import os
os.environ["DD_TRACE_ENABLED"] = "false"
os.environ["DATADOG_TRACE_ENABLED"] = "false"

# Colors for output
CYAN = "\033[0;36m"
GREEN = "\033[0;32m"
RED = "\033[0;31m"
YELLOW = "\033[0;33m"
NC = "\033[0m"  # No Color


def test_package_import(package_name: str, import_name: str = None) -> Tuple[bool, str]:
    """Test if a package can be imported."""
    import_name = import_name or package_name.replace("-", "_")
    try:
        cmd = [sys.executable, "-c", f"import {import_name}; print('{import_name} imported successfully')"]
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=10)
        if result.returncode == 0:
            return True, result.stdout.strip()
        else:
            return False, result.stderr.strip()
    except Exception as e:
        return False, str(e)


def test_package_version(package_name: str) -> Tuple[bool, str]:
    """Test if we can get the package version."""
    try:
        cmd = [sys.executable, "-m", "pip", "show", package_name]
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=10)
        if result.returncode == 0:
            for line in result.stdout.split("\n"):
                if line.startswith("Version:"):
                    return True, line.split(":")[1].strip()
        return False, "Version not found"
    except Exception as e:
        return False, str(e)


def main():
    """Main test function."""
    print(f"{CYAN}Hanzo Python SDK Monorepo Health Check{NC}\n")
    
    packages = [
        ("hanzoai", "hanzoai"),
        ("hanzo-agents", "hanzo_agents"),
        ("hanzo-mcp", "hanzo_mcp"),
        ("hanzo-cli", "hanzo_cli"),
        ("hanzo-repl", "hanzo_repl"),
        ("hanzo-memory", "hanzo_memory"),
        ("hanzo-network", "hanzo_network"),
        ("hanzo-mcp-client", "hanzo_mcp_client"),
        ("hanzo-aci", "dev_aci"),  # Note: This publishes as dev-aci
    ]
    
    all_passed = True
    results = []
    
    for package_name, import_name in packages:
        print(f"\n{GREEN}Testing {package_name}...{NC}")
        
        # Test import
        import_success, import_msg = test_package_import(package_name, import_name)
        if import_success:
            print(f"  ✓ Import: {import_msg}")
        else:
            print(f"  {RED}✗ Import failed: {import_msg}{NC}")
            all_passed = False
        
        # Test version
        version_success, version = test_package_version(package_name)
        if version_success:
            print(f"  ✓ Version: {version}")
        else:
            print(f"  {YELLOW}⚠ Version check failed: {version}{NC}")
        
        results.append({
            "package": package_name,
            "import_success": import_success,
            "version": version if version_success else None
        })
    
    # Summary
    print(f"\n{CYAN}Summary:{NC}")
    successful = sum(1 for r in results if r["import_success"])
    print(f"  Packages tested: {len(results)}")
    print(f"  Successful imports: {successful}")
    print(f"  Failed imports: {len(results) - successful}")
    
    if all_passed:
        print(f"\n{GREEN}✅ All packages are healthy!{NC}")
    else:
        print(f"\n{RED}❌ Some packages have issues.{NC}")
        print(f"\nFailed packages:")
        for r in results:
            if not r["import_success"]:
                print(f"  - {r['package']}")
    
    # Test PostHog availability
    print(f"\n{CYAN}Analytics Check:{NC}")
    try:
        from hanzo_mcp.analytics import Analytics
        print(f"  {GREEN}✓ PostHog analytics available in hanzo-mcp{NC}")
    except ImportError:
        print(f"  {YELLOW}⚠ PostHog analytics not available{NC}")
    
    return 0 if all_passed else 1


if __name__ == "__main__":
    sys.exit(main())