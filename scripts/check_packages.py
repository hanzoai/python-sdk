#!/usr/bin/env python3
"""Check package configurations in the monorepo."""

import os
import sys
import tomllib
from pathlib import Path
from typing import Dict, List, Tuple

# ANSI color codes
CYAN = "\033[0;36m"
GREEN = "\033[0;32m"
RED = "\033[0;31m"
YELLOW = "\033[0;33m"
NC = "\033[0m"  # No Color


def check_package(pkg_path: Path) -> Tuple[str, List[str], List[str]]:
    """Check a single package configuration."""
    issues = []
    warnings = []
    
    pyproject_path = pkg_path / "pyproject.toml"
    
    if not pyproject_path.exists():
        return str(pkg_path), [f"Missing pyproject.toml"], warnings
    
    try:
        with open(pyproject_path, "rb") as f:
            config = tomllib.load(f)
    except Exception as e:
        return str(pkg_path), [f"Failed to parse pyproject.toml: {e}"], warnings
    
    # Check project metadata
    project = config.get("project", {})
    if not project.get("name"):
        issues.append("Missing project.name")
    if not project.get("version"):
        issues.append("Missing project.version")
    if not project.get("description"):
        warnings.append("Missing project.description")
    
    # Check build system
    build_system = config.get("build-system", {})
    if not build_system:
        issues.append("Missing [build-system] section")
    else:
        backend = build_system.get("build-backend")
        if not backend:
            issues.append("Missing build-backend")
        elif backend not in ["hatchling.build", "setuptools.build_meta"]:
            warnings.append(f"Non-standard build backend: {backend}")
    
    # Check Python version requirement
    requires_python = project.get("requires-python")
    if not requires_python:
        warnings.append("Missing requires-python")
    
    # Check for dist directory (built packages)
    dist_path = pkg_path / "dist"
    if not dist_path.exists():
        warnings.append("Package not built (no dist/ directory)")
    
    # Check for tests
    test_paths = [pkg_path / "tests", pkg_path / "test"]
    if not any(p.exists() for p in test_paths):
        warnings.append("No tests directory found")
    
    # Check package name consistency
    pkg_name = project.get("name", "")
    expected_name = pkg_path.name
    if pkg_name and expected_name.startswith("hanzo-") and pkg_name != expected_name:
        issues.append(f"Package name mismatch: {pkg_name} != {expected_name}")
    
    return str(pkg_path), issues, warnings


def main():
    """Check all packages in the monorepo."""
    print(f"{CYAN}Checking package configurations...{NC}\n")
    
    # Find all packages
    pkg_dir = Path("pkg")
    packages = []
    
    # Add main package
    packages.append(Path("."))
    
    # Add all subdirectories in pkg/
    if pkg_dir.exists():
        for item in pkg_dir.iterdir():
            if item.is_dir() and (item / "pyproject.toml").exists():
                packages.append(item)
    
    all_issues = []
    all_warnings = []
    
    for pkg_path in sorted(packages):
        pkg_name, issues, warnings = check_package(pkg_path)
        
        print(f"{GREEN}📦 {pkg_name}{NC}")
        
        if issues:
            all_issues.extend([(pkg_name, issue) for issue in issues])
            for issue in issues:
                print(f"  {RED}✗ {issue}{NC}")
        
        if warnings:
            all_warnings.extend([(pkg_name, warning) for warning in warnings])
            for warning in warnings:
                print(f"  {YELLOW}⚠ {warning}{NC}")
        
        if not issues and not warnings:
            print(f"  {GREEN}✓ All checks passed{NC}")
        
        print()
    
    # Summary
    print(f"\n{CYAN}Summary:{NC}")
    print(f"  Packages checked: {len(packages)}")
    print(f"  Issues found: {len(all_issues)}")
    print(f"  Warnings found: {len(all_warnings)}")
    
    if all_issues:
        print(f"\n{RED}❌ Fix these issues before publishing:{NC}")
        for pkg, issue in all_issues:
            print(f"  {pkg}: {issue}")
        sys.exit(1)
    else:
        print(f"\n{GREEN}✅ All packages ready for publishing!{NC}")
        
    if all_warnings:
        print(f"\n{YELLOW}⚠️  Consider addressing these warnings:{NC}")
        for pkg, warning in all_warnings[:5]:  # Show first 5 warnings
            print(f"  {pkg}: {warning}")
        if len(all_warnings) > 5:
            print(f"  ... and {len(all_warnings) - 5} more")


if __name__ == "__main__":
    main()