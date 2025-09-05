#!/usr/bin/env python3
"""
Check package versions and publish to PyPI if newer version is available.
This script is designed to run in CI on every push to main.
"""

import os
import re
import sys
import json
import subprocess
import urllib.error
import urllib.request
from typing import Tuple, Optional
from pathlib import Path

# Colors for output
RED = "\033[0;31m"
GREEN = "\033[0;32m"
YELLOW = "\033[1;33m"
BLUE = "\033[0;34m"
NC = "\033[0m"  # No Color


def print_info(msg: str):
    print(f"{GREEN}[INFO]{NC} {msg}")


def print_warn(msg: str):
    print(f"{YELLOW}[WARN]{NC} {msg}")


def print_error(msg: str):
    print(f"{RED}[ERROR]{NC} {msg}")


def print_action(msg: str):
    print(f"{BLUE}[ACTION]{NC} {msg}")


def get_local_version(package_dir: Path) -> Optional[str]:
    """Extract version from pyproject.toml."""
    pyproject_path = package_dir / "pyproject.toml"
    if not pyproject_path.exists():
        return None

    with open(pyproject_path, "r") as f:
        content = f.read()

    # Match version = "x.y.z" or version = 'x.y.z'
    match = re.search(r'version\s*=\s*["\']([^"\']+)["\']', content)
    if match:
        return match.group(1)
    return None


def get_pypi_version(package_name: str) -> Optional[str]:
    """Get the latest version from PyPI."""
    url = f"https://pypi.org/pypi/{package_name}/json"
    try:
        with urllib.request.urlopen(url, timeout=30) as response:  # noqa: S310
            data = json.loads(response.read())
            return data.get("info", {}).get("version")
    except urllib.error.HTTPError as e:
        if e.code == 404:
            # Package doesn't exist on PyPI yet
            return None
        raise
    except Exception as e:
        print_warn(f"Could not fetch PyPI version for {package_name}: {e}")
        return None


def parse_version(version: str) -> Tuple[int, ...]:
    """Parse version string to tuple for comparison."""
    # Remove any pre-release or build metadata
    version = re.split(r"[-+]", version)[0]
    return tuple(int(x) for x in version.split("."))


def is_newer_version(local_version: str, pypi_version: Optional[str]) -> bool:
    """Check if local version is newer than PyPI version."""
    if pypi_version is None:
        # Package doesn't exist on PyPI
        return True

    try:
        local_tuple = parse_version(local_version)
        pypi_tuple = parse_version(pypi_version)
        return local_tuple > pypi_tuple
    except (ValueError, AttributeError):
        # If we can't parse versions, compare as strings
        return local_version != pypi_version


def build_package(package_dir: Path) -> bool:
    """Build the Python package."""
    print_info(f"Building package in {package_dir}")

    # Clean previous builds
    for dir_name in ["dist", "build"]:
        dir_path = package_dir / dir_name
        if dir_path.exists():
            subprocess.run(["rm", "-rf", str(dir_path)], check=True)

    # Remove .egg-info directories
    for egg_info in package_dir.glob("*.egg-info"):
        subprocess.run(["rm", "-rf", str(egg_info)], check=True)

    # Build the package
    result = subprocess.run(
        ["python", "-m", "build"], cwd=package_dir, capture_output=True, text=True
    )

    if result.returncode != 0:
        print_error(f"Build failed: {result.stderr}")
        return False

    return True


def publish_package(package_dir: Path, package_name: str) -> bool:
    """Publish package to PyPI."""
    print_action(f"Publishing {package_name} to PyPI")

    # Check for PyPI token
    pypi_token = os.environ.get("PYPI_TOKEN") or os.environ.get("HANZO_PYPI_TOKEN")
    if not pypi_token:
        print_error("PYPI_TOKEN or HANZO_PYPI_TOKEN environment variable not set")
        return False

    # Upload to PyPI
    result = subprocess.run(
        ["python", "-m", "twine", "upload", "dist/*", "--skip-existing"],
        cwd=package_dir,
        env={**os.environ, "TWINE_USERNAME": "__token__", "TWINE_PASSWORD": pypi_token},
        capture_output=True,
        text=True,
    )

    if result.returncode != 0:
        print_error(f"Upload failed: {result.stderr}")
        return False

    print_info(f"✅ Successfully published {package_name}")
    return True


def check_and_publish_package(package_name: str, package_dir: Path) -> bool:
    """Check version and publish if newer."""
    print_info(f"Checking {package_name}...")

    # Get local version
    local_version = get_local_version(package_dir)
    if not local_version:
        print_warn(f"Could not find version for {package_name}")
        return False

    print_info(f"  Local version: {local_version}")

    # Get PyPI version
    pypi_version = get_pypi_version(package_name)
    if pypi_version:
        print_info(f"  PyPI version:  {pypi_version}")
    else:
        print_info(f"  PyPI version:  Not published yet")

    # Check if we need to publish
    if is_newer_version(local_version, pypi_version):
        print_action(f"📦 New version detected for {package_name}: {local_version}")

        # Build the package
        if not build_package(package_dir):
            return False

        # Publish to PyPI
        return publish_package(package_dir, package_name)
    else:
        print_info(f"  ✓ {package_name} is up to date")
        return True


def main():
    """Main function to check and publish all packages."""
    # Define packages in dependency order
    packages = [
        "hanzo-network",
        "hanzo-memory",
        "hanzo-agents",
        "hanzo-aci",
        "hanzo-mcp",
        "hanzo-repl",
        "hanzo",
    ]

    # Get repository root
    script_dir = Path(__file__).parent
    repo_root = script_dir.parent
    pkg_dir = repo_root / "pkg"

    # Install required tools
    print_info("Installing build tools...")
    try:
        # Try with pip first
        subprocess.run(
            [
                sys.executable,
                "-m",
                "pip",
                "install",
                "--quiet",
                "--upgrade",
                "pip",
                "build",
                "twine",
            ],
            check=True,
            capture_output=True,
        )
    except (subprocess.CalledProcessError, FileNotFoundError):
        # Fall back to installing without pip upgrade
        try:
            subprocess.run(
                [sys.executable, "-m", "pip", "install", "--quiet", "build", "twine"],
                check=True,
                capture_output=True,
            )
        except Exception:
            print_warn(
                "Could not install build tools. Make sure pip, build, and twine are available."
            )
            print_info("You can install them with: pip install build twine")

    # Track results
    published = []
    failed = []
    skipped = []

    # Check and publish each package
    for package_name in packages:
        package_dir = pkg_dir / package_name

        if not package_dir.exists():
            print_warn(f"Package directory {package_dir} does not exist")
            skipped.append(package_name)
            continue

        try:
            local_version = get_local_version(package_dir)
            pypi_version = get_pypi_version(package_name)

            if is_newer_version(local_version, pypi_version):
                if check_and_publish_package(package_name, package_dir):
                    published.append(f"{package_name} ({local_version})")
                else:
                    failed.append(package_name)
            else:
                skipped.append(f"{package_name} (already at {local_version})")
        except Exception as e:
            print_error(f"Error processing {package_name}: {e}")
            failed.append(package_name)

    # Print summary
    print("\n" + "=" * 60)
    print("📊 SUMMARY")
    print("=" * 60)

    if published:
        print(f"\n{GREEN}✅ Published ({len(published)}):{NC}")
        for pkg in published:
            print(f"  • {pkg}")

    if skipped:
        print(f"\n{BLUE}⏭️  Skipped ({len(skipped)}):{NC}")
        for pkg in skipped:
            print(f"  • {pkg}")

    if failed:
        print(f"\n{RED}❌ Failed ({len(failed)}):{NC}")
        for pkg in failed:
            print(f"  • {pkg}")
        sys.exit(1)

    # Set GitHub Actions output if running in CI
    if os.environ.get("GITHUB_ACTIONS"):
        if published:
            print(
                f"::notice title=Published Packages::Published {len(published)} packages to PyPI: {', '.join(published)}"
            )
        else:
            print("::notice title=No Updates::All packages are up to date on PyPI")

    print(f"\n{GREEN}✨ All packages processed successfully!{NC}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
