"""Hanzo Install - Cross-platform tool installation CLI.

Install Hanzo tools from PyPI, npm, cargo, and GitHub releases.
"""

import os
import sys
import platform
import subprocess
import shutil
from pathlib import Path
from typing import Optional, List, Dict

import click
from rich import box
from rich.table import Table
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn

from ..utils.output import console


# ============================================================================
# Tool Registry
# ============================================================================

TOOLS = {
    # Python tools (PyPI)
    "cli": {
        "name": "Hanzo CLI",
        "description": "Python CLI for Hanzo AI platform",
        "source": "pypi",
        "package": "hanzo",
        "extras": ["all"],
        "binary": "hanzo",
        "language": "python",
    },
    "mcp": {
        "name": "Hanzo MCP",
        "description": "Model Context Protocol server",
        "source": "pypi",
        "package": "hanzo-mcp",
        "extras": ["tools-all"],
        "binary": "hanzo-mcp",
        "language": "python",
    },
    "agents": {
        "name": "Hanzo Agents",
        "description": "Multi-agent orchestration framework",
        "source": "pypi",
        "package": "hanzo-agents",
        "binary": "hanzo-agents",
        "language": "python",
    },
    "ai": {
        "name": "Hanzo AI SDK",
        "description": "Python SDK for Hanzo AI APIs",
        "source": "pypi",
        "package": "hanzoai",
        "binary": None,
        "language": "python",
    },
    # JavaScript/TypeScript tools (npm)
    "cli-js": {
        "name": "Hanzo CLI (JS)",
        "description": "JavaScript CLI for container runtime",
        "source": "npm",
        "package": "@hanzoai/cli",
        "binary": "hanzo-js",
        "language": "javascript",
    },
    "mcp-js": {
        "name": "Hanzo MCP (JS)",
        "description": "JavaScript MCP implementation",
        "source": "npm",
        "package": "@anthropic/mcp",  # Uses official MCP
        "binary": None,
        "language": "javascript",
    },
    # Rust tools (cargo/GitHub releases)
    "node": {
        "name": "Hanzo Node",
        "description": "Rust-based AI compute node",
        "source": "github",
        "repo": "hanzoai/node",
        "binary": "hanzo-node",
        "language": "rust",
        "cargo": "hanzo-node",
    },
    "dev": {
        "name": "Hanzo Dev",
        "description": "Rust AI coding assistant (Codex)",
        "source": "github",
        "repo": "hanzoai/dev",
        "binary": "hanzo-dev",
        "language": "rust",
        "cargo": "hanzo-dev",
    },
    "mcp-rs": {
        "name": "Hanzo MCP (Rust)",
        "description": "High-performance Rust MCP server",
        "source": "github",
        "repo": "hanzoai/mcp-rs",
        "binary": "hanzo-mcp-rs",
        "language": "rust",
        "cargo": "hanzo-mcp",
    },
    # Go tools (go install)
    "router": {
        "name": "Hanzo Router",
        "description": "LLM Gateway/Router (LiteLLM proxy)",
        "source": "docker",
        "image": "ghcr.io/hanzoai/llm:latest",
        "binary": None,
        "language": "go",
    },
}

# Tool bundles
BUNDLES = {
    "minimal": ["cli"],
    "python": ["cli", "mcp", "agents", "ai"],
    "rust": ["node", "dev", "mcp-rs"],
    "javascript": ["cli-js", "mcp-js"],
    "full": ["cli", "mcp", "agents", "ai", "node", "dev"],
    "dev": ["cli", "mcp", "dev"],
    "cloud": ["cli", "mcp", "router"],
}


def get_arch() -> str:
    """Get system architecture for binary downloads."""
    machine = platform.machine().lower()
    if machine in ("x86_64", "amd64"):
        return "x86_64"
    elif machine in ("arm64", "aarch64"):
        return "aarch64"
    elif machine in ("arm", "armv7l"):
        return "arm"
    return machine


def get_os() -> str:
    """Get OS name for binary downloads."""
    system = platform.system().lower()
    if system == "darwin":
        return "apple-darwin"
    elif system == "linux":
        return "unknown-linux-gnu"
    elif system == "windows":
        return "pc-windows-msvc"
    return system


def get_install_dir() -> Path:
    """Get installation directory for binaries."""
    # Check for custom install dir
    if custom_dir := os.environ.get("HANZO_INSTALL_DIR"):
        return Path(custom_dir)

    # Default to ~/.hanzo/bin
    return Path.home() / ".hanzo" / "bin"


def ensure_path_configured():
    """Ensure ~/.hanzo/bin is in PATH."""
    install_dir = get_install_dir()
    install_dir.mkdir(parents=True, exist_ok=True)

    path = os.environ.get("PATH", "")
    if str(install_dir) not in path:
        shell = os.environ.get("SHELL", "/bin/bash")
        if "zsh" in shell:
            rc_file = Path.home() / ".zshrc"
        elif "bash" in shell:
            rc_file = Path.home() / ".bashrc"
        else:
            rc_file = Path.home() / ".profile"

        export_line = f'\nexport PATH="$HOME/.hanzo/bin:$PATH"\n'

        # Check if already configured
        if rc_file.exists():
            content = rc_file.read_text()
            if ".hanzo/bin" not in content:
                with open(rc_file, "a") as f:
                    f.write(export_line)
                return True
    return False


@click.group(name="install")
def install_group():
    """Hanzo Install - Tool installation manager.

    \b
    Quick Install:
      hanzo install all              # Install all tools
      hanzo install cli              # Install Python CLI
      hanzo install node             # Install Rust node

    \b
    Bundles:
      hanzo install --bundle python  # Python tools (cli, mcp, agents, ai)
      hanzo install --bundle rust    # Rust tools (node, dev, mcp-rs)
      hanzo install --bundle dev     # Development tools

    \b
    Management:
      hanzo install list             # List installed tools
      hanzo install update           # Update all tools
      hanzo install uninstall <tool> # Remove a tool

    \b
    Environment Variables:
      HANZO_INSTALL_DIR     # Custom install directory
      HANZO_PREFER_RUST     # Prefer Rust implementations
      HANZO_PREFER_SOURCE   # Build from source vs binaries
    """
    pass


@install_group.command(name="list")
@click.option("--installed", "-i", is_flag=True, help="Show only installed tools")
@click.option("--available", "-a", is_flag=True, help="Show only available tools")
def install_list(installed: bool, available: bool):
    """List all Hanzo tools."""
    table = Table(title="Hanzo Tools", box=box.ROUNDED)
    table.add_column("Tool", style="cyan")
    table.add_column("Name", style="white")
    table.add_column("Language", style="yellow")
    table.add_column("Source", style="green")
    table.add_column("Installed", style="green")
    table.add_column("Version", style="dim")

    for tool_id, tool in TOOLS.items():
        # Check if installed
        is_installed = False
        version = "-"

        if binary := tool.get("binary"):
            is_installed = shutil.which(binary) is not None
            if is_installed:
                try:
                    result = subprocess.run(
                        [binary, "--version"],
                        capture_output=True,
                        text=True,
                        timeout=5
                    )
                    version = result.stdout.strip().split()[-1] if result.returncode == 0 else "?"
                except:
                    version = "?"

        if installed and not is_installed:
            continue
        if available and is_installed:
            continue

        table.add_row(
            tool_id,
            tool["name"],
            tool["language"],
            tool["source"],
            "✓" if is_installed else "",
            version
        )

    console.print(table)

    console.print()
    console.print("[cyan]Bundles:[/cyan]")
    for bundle_id, tools in BUNDLES.items():
        console.print(f"  {bundle_id}: {', '.join(tools)}")


@install_group.command(name="tool")
@click.argument("tool_name")
@click.option("--version", "-v", help="Specific version")
@click.option("--source", "-s", is_flag=True, help="Build from source")
@click.option("--force", "-f", is_flag=True, help="Force reinstall")
def install_tool(tool_name: str, version: str, source: bool, force: bool):
    """Install a specific tool.

    \b
    Examples:
      hanzo install tool cli
      hanzo install tool node --version 0.1.0
      hanzo install tool dev --source
    """
    if tool_name == "all":
        # Install all tools
        for tid in TOOLS:
            _install_single_tool(tid, version, source, force)
        return

    if tool_name not in TOOLS:
        console.print(f"[red]Unknown tool: {tool_name}[/red]")
        console.print(f"Available: {', '.join(TOOLS.keys())}")
        return

    _install_single_tool(tool_name, version, source, force)


def _install_single_tool(tool_id: str, version: str, source: bool, force: bool):
    """Install a single tool."""
    tool = TOOLS[tool_id]

    console.print(f"[cyan]Installing {tool['name']}...[/cyan]")

    try:
        if tool["source"] == "pypi":
            _install_pypi(tool, version, force)
        elif tool["source"] == "npm":
            _install_npm(tool, version, force)
        elif tool["source"] == "github":
            if source or os.environ.get("HANZO_PREFER_SOURCE"):
                _install_cargo(tool, version, force)
            else:
                _install_github_release(tool, version, force)
        elif tool["source"] == "docker":
            _install_docker(tool, version, force)
        else:
            console.print(f"[yellow]Unknown source: {tool['source']}[/yellow]")
            return

        console.print(f"[green]✓[/green] {tool['name']} installed")

    except Exception as e:
        console.print(f"[red]Failed to install {tool['name']}: {e}[/red]")


def _install_pypi(tool: dict, version: str, force: bool):
    """Install from PyPI using uvx/pip."""
    package = tool["package"]
    extras = tool.get("extras", [])

    if extras:
        package = f"{package}[{','.join(extras)}]"
    if version:
        package = f"{package}=={version}"

    # Prefer uvx/uv, fallback to pip
    if shutil.which("uv"):
        cmd = ["uv", "pip", "install"]
        if force:
            cmd.append("--force-reinstall")
        cmd.append(package)
    else:
        cmd = [sys.executable, "-m", "pip", "install"]
        if force:
            cmd.append("--force-reinstall")
        cmd.append(package)

    subprocess.run(cmd, check=True)


def _install_npm(tool: dict, version: str, force: bool):
    """Install from npm."""
    package = tool["package"]
    if version:
        package = f"{package}@{version}"

    cmd = ["npm", "install", "-g"]
    if force:
        cmd.append("--force")
    cmd.append(package)

    subprocess.run(cmd, check=True)


def _install_cargo(tool: dict, version: str, force: bool):
    """Install from cargo (build from source)."""
    package = tool.get("cargo", tool["package"])

    cmd = ["cargo", "install"]
    if force:
        cmd.append("--force")
    if version:
        cmd.extend(["--version", version])
    cmd.append(package)

    subprocess.run(cmd, check=True)


def _install_github_release(tool: dict, version: str, force: bool):
    """Install pre-built binary from GitHub releases."""
    import urllib.request
    import tempfile
    import tarfile
    import zipfile

    repo = tool["repo"]
    binary = tool["binary"]

    # Get latest release if no version specified
    if not version:
        api_url = f"https://api.github.com/repos/{repo}/releases/latest"
        with urllib.request.urlopen(api_url) as response:
            import json
            data = json.loads(response.read())
            version = data["tag_name"].lstrip("v")

    # Determine asset name
    arch = get_arch()
    os_name = get_os()

    # Common patterns for release assets
    patterns = [
        f"{binary}-{version}-{arch}-{os_name}",
        f"{binary}-{arch}-{os_name}",
        f"{binary}-{os_name}-{arch}",
    ]

    # Get release assets
    api_url = f"https://api.github.com/repos/{repo}/releases/tags/v{version}"
    try:
        with urllib.request.urlopen(api_url) as response:
            import json
            data = json.loads(response.read())
    except:
        api_url = f"https://api.github.com/repos/{repo}/releases/tags/{version}"
        with urllib.request.urlopen(api_url) as response:
            import json
            data = json.loads(response.read())

    # Find matching asset
    download_url = None
    for asset in data.get("assets", []):
        name = asset["name"].lower()
        for pattern in patterns:
            if pattern.lower() in name:
                download_url = asset["browser_download_url"]
                break
        if download_url:
            break

    if not download_url:
        console.print(f"[yellow]No pre-built binary found, building from source...[/yellow]")
        _install_cargo(tool, version, force)
        return

    # Download and extract
    install_dir = get_install_dir()
    install_dir.mkdir(parents=True, exist_ok=True)

    with tempfile.TemporaryDirectory() as tmpdir:
        tmppath = Path(tmpdir)
        archive_path = tmppath / "archive"

        console.print(f"  Downloading from {download_url}...")
        urllib.request.urlretrieve(download_url, archive_path)

        # Extract
        if download_url.endswith(".tar.gz") or download_url.endswith(".tgz"):
            with tarfile.open(archive_path, "r:gz") as tar:
                tar.extractall(tmppath)
        elif download_url.endswith(".zip"):
            with zipfile.ZipFile(archive_path, "r") as z:
                z.extractall(tmppath)
        else:
            # Assume it's a raw binary
            shutil.copy(archive_path, install_dir / binary)
            os.chmod(install_dir / binary, 0o755)
            return

        # Find the binary in extracted files
        for f in tmppath.rglob("*"):
            if f.is_file() and f.name == binary:
                shutil.copy(f, install_dir / binary)
                os.chmod(install_dir / binary, 0o755)
                break

    ensure_path_configured()


def _install_docker(tool: dict, version: str, force: bool):
    """Pull Docker image."""
    image = tool["image"]
    if version:
        image = image.replace(":latest", f":{version}")

    subprocess.run(["docker", "pull", image], check=True)


@install_group.command(name="bundle")
@click.argument("bundle_name")
@click.option("--force", "-f", is_flag=True, help="Force reinstall")
def install_bundle(bundle_name: str, force: bool):
    """Install a bundle of tools.

    \b
    Bundles:
      minimal    - Just the Python CLI
      python     - All Python tools (cli, mcp, agents, ai)
      rust       - All Rust tools (node, dev, mcp-rs)
      javascript - All JS tools (cli-js, mcp-js)
      full       - Everything
      dev        - Development tools (cli, mcp, dev)
      cloud      - Cloud deployment tools
    """
    if bundle_name not in BUNDLES:
        console.print(f"[red]Unknown bundle: {bundle_name}[/red]")
        console.print(f"Available: {', '.join(BUNDLES.keys())}")
        return

    tools = BUNDLES[bundle_name]
    console.print(f"[cyan]Installing bundle '{bundle_name}': {', '.join(tools)}[/cyan]")
    console.print()

    for tool_id in tools:
        _install_single_tool(tool_id, None, False, force)
        console.print()


@install_group.command(name="update")
@click.option("--tool", "-t", help="Update specific tool")
def install_update(tool: str):
    """Update installed tools."""
    if tool:
        if tool not in TOOLS:
            console.print(f"[red]Unknown tool: {tool}[/red]")
            return
        _install_single_tool(tool, None, False, True)
    else:
        console.print("[cyan]Updating all installed tools...[/cyan]")
        for tool_id, tool_info in TOOLS.items():
            if binary := tool_info.get("binary"):
                if shutil.which(binary):
                    _install_single_tool(tool_id, None, False, True)


@install_group.command(name="uninstall")
@click.argument("tool_name")
def install_uninstall(tool_name: str):
    """Uninstall a tool."""
    if tool_name not in TOOLS:
        console.print(f"[red]Unknown tool: {tool_name}[/red]")
        return

    tool = TOOLS[tool_name]

    try:
        if tool["source"] == "pypi":
            cmd = [sys.executable, "-m", "pip", "uninstall", "-y", tool["package"]]
            subprocess.run(cmd, check=True)
        elif tool["source"] == "npm":
            subprocess.run(["npm", "uninstall", "-g", tool["package"]], check=True)
        elif tool["source"] == "github":
            # Remove binary
            install_dir = get_install_dir()
            binary_path = install_dir / tool["binary"]
            if binary_path.exists():
                binary_path.unlink()

        console.print(f"[green]✓[/green] {tool['name']} uninstalled")
    except Exception as e:
        console.print(f"[red]Failed to uninstall: {e}[/red]")


@install_group.command(name="script")
@click.option("--output", "-o", help="Output file (default: stdout)")
def install_script(output: str):
    """Generate install.sh script for quick installation.

    \b
    Usage:
      curl -fsSL https://hanzo.sh/install | bash
      hanzo install script > install.sh
    """
    script = '''#!/usr/bin/env bash
# Hanzo AI - Universal Installer
# https://hanzo.ai
#
# Usage:
#   curl -fsSL https://hanzo.sh/install | bash
#   curl -fsSL https://hanzo.sh/install | bash -s -- --bundle rust
#   HANZO_PREFER_RUST=1 curl -fsSL https://hanzo.sh/install | bash

set -euo pipefail

# Colors
RED='\\033[0;31m'
GREEN='\\033[0;32m'
CYAN='\\033[0;36m'
NC='\\033[0m'

info() { echo -e "${CYAN}$1${NC}"; }
success() { echo -e "${GREEN}✓ $1${NC}"; }
error() { echo -e "${RED}✗ $1${NC}"; exit 1; }

# Configuration
BUNDLE="${HANZO_BUNDLE:-minimal}"
INSTALL_DIR="${HANZO_INSTALL_DIR:-$HOME/.hanzo/bin}"
PREFER_RUST="${HANZO_PREFER_RUST:-0}"

# Parse args
while [[ $# -gt 0 ]]; do
    case $1 in
        --bundle) BUNDLE="$2"; shift 2 ;;
        --rust) PREFER_RUST=1; shift ;;
        --dir) INSTALL_DIR="$2"; shift 2 ;;
        *) shift ;;
    esac
done

info "Hanzo AI Installer"
info "=================="
echo ""
info "Bundle: $BUNDLE"
info "Install dir: $INSTALL_DIR"
echo ""

# Create install directory
mkdir -p "$INSTALL_DIR"

# Detect OS and arch
OS=$(uname -s | tr '[:upper:]' '[:lower:]')
ARCH=$(uname -m)

case "$ARCH" in
    x86_64|amd64) ARCH="x86_64" ;;
    arm64|aarch64) ARCH="aarch64" ;;
    *) error "Unsupported architecture: $ARCH" ;;
esac

case "$OS" in
    darwin) OS_NAME="apple-darwin" ;;
    linux) OS_NAME="unknown-linux-gnu" ;;
    *) error "Unsupported OS: $OS" ;;
esac

# Check for uv/uvx
install_uv() {
    if ! command -v uv &> /dev/null; then
        info "Installing uv (Python package manager)..."
        curl -LsSf https://astral.sh/uv/install.sh | sh
        export PATH="$HOME/.cargo/bin:$PATH"
    fi
    success "uv available"
}

# Install Python tools
install_python() {
    install_uv

    info "Installing Python tools..."

    case "$BUNDLE" in
        minimal|python|full|dev|cloud)
            uv pip install hanzo[all]
            success "hanzo CLI installed"
            ;;
    esac

    case "$BUNDLE" in
        python|full|dev|cloud)
            uv pip install hanzo-mcp[tools-all]
            success "hanzo-mcp installed"
            ;;
    esac

    case "$BUNDLE" in
        python|full)
            uv pip install hanzo-agents
            success "hanzo-agents installed"
            ;;
    esac
}

# Install Rust tools from GitHub releases
install_rust_binary() {
    local repo="$1"
    local binary="$2"
    local version="${3:-latest}"

    info "Installing $binary..."

    if [[ "$version" == "latest" ]]; then
        version=$(curl -s "https://api.github.com/repos/$repo/releases/latest" | grep '"tag_name"' | cut -d'"' -f4)
    fi

    local url="https://github.com/$repo/releases/download/$version/${binary}-${ARCH}-${OS_NAME}.tar.gz"

    if curl -fsSL "$url" -o "/tmp/${binary}.tar.gz" 2>/dev/null; then
        tar -xzf "/tmp/${binary}.tar.gz" -C "$INSTALL_DIR"
        chmod +x "$INSTALL_DIR/$binary"
        success "$binary installed"
    else
        info "Pre-built binary not found, building from source..."
        if command -v cargo &> /dev/null; then
            cargo install --git "https://github.com/$repo"
            success "$binary installed (from source)"
        else
            error "Cargo not found. Install Rust: https://rustup.rs"
        fi
    fi
}

# Install Rust tools
install_rust() {
    case "$BUNDLE" in
        rust|full)
            install_rust_binary "hanzoai/node" "hanzo-node"
            install_rust_binary "hanzoai/dev" "hanzo-dev"
            ;;
    esac

    case "$BUNDLE" in
        dev)
            install_rust_binary "hanzoai/dev" "hanzo-dev"
            ;;
    esac
}

# Add to PATH
configure_path() {
    local shell_rc=""

    case "$SHELL" in
        */zsh) shell_rc="$HOME/.zshrc" ;;
        */bash) shell_rc="$HOME/.bashrc" ;;
        *) shell_rc="$HOME/.profile" ;;
    esac

    if ! grep -q ".hanzo/bin" "$shell_rc" 2>/dev/null; then
        echo 'export PATH="$HOME/.hanzo/bin:$PATH"' >> "$shell_rc"
        info "Added ~/.hanzo/bin to PATH in $shell_rc"
    fi
}

# Main
main() {
    install_python

    if [[ "$PREFER_RUST" == "1" ]] || [[ "$BUNDLE" == "rust" ]] || [[ "$BUNDLE" == "full" ]]; then
        install_rust
    fi

    configure_path

    echo ""
    success "Hanzo AI installed successfully!"
    echo ""
    info "Run: source ~/.zshrc  # or restart your terminal"
    info "Then: hanzo --help"
}

main "$@"
'''

    if output:
        with open(output, "w") as f:
            f.write(script)
        os.chmod(output, 0o755)
        console.print(f"[green]✓[/green] Install script written to {output}")
    else:
        console.print(script)


@install_group.command(name="doctor")
def install_doctor():
    """Check installation health and dependencies."""
    console.print("[cyan]Hanzo Installation Health Check[/cyan]")
    console.print()

    checks = [
        ("Python", "python3 --version", "3.12+"),
        ("uv", "uv --version", "0.4+"),
        ("Node.js", "node --version", "18+"),
        ("npm", "npm --version", "9+"),
        ("Rust", "rustc --version", "1.75+"),
        ("Cargo", "cargo --version", "1.75+"),
        ("Docker", "docker --version", "24+"),
        ("Git", "git --version", "2.30+"),
    ]

    for name, cmd, required in checks:
        try:
            result = subprocess.run(
                cmd.split(),
                capture_output=True,
                text=True,
                timeout=5
            )
            if result.returncode == 0:
                version = result.stdout.strip().split()[-1]
                console.print(f"  [green]✓[/green] {name}: {version}")
            else:
                console.print(f"  [yellow]![/yellow] {name}: not found (optional)")
        except:
            console.print(f"  [yellow]![/yellow] {name}: not found")

    console.print()

    # Check Hanzo tools
    console.print("[cyan]Hanzo Tools:[/cyan]")
    for tool_id, tool in TOOLS.items():
        if binary := tool.get("binary"):
            if shutil.which(binary):
                console.print(f"  [green]✓[/green] {tool['name']} ({binary})")
            else:
                console.print(f"  [dim]○[/dim] {tool['name']} (not installed)")

    console.print()

    # Check PATH
    install_dir = get_install_dir()
    if str(install_dir) in os.environ.get("PATH", ""):
        console.print(f"[green]✓[/green] {install_dir} is in PATH")
    else:
        console.print(f"[yellow]![/yellow] {install_dir} is NOT in PATH")
        console.print(f"  Add to your shell config: export PATH=\"{install_dir}:$PATH\"")
