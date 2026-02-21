"""Hanzo Install - Cross-platform tool installation CLI.

Install Hanzo tools from PyPI, npm, cargo, and GitHub releases.
"""

import os
import sys
import shutil
import platform
import subprocess
from typing import Dict, List, Optional
from pathlib import Path

import click
from rich import box
from rich.panel import Panel
from rich.table import Table
from rich.progress import Progress, BarColumn, TextColumn, SpinnerColumn

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
                    result = subprocess.run([binary, "--version"], capture_output=True, text=True, timeout=5)
                    version = result.stdout.strip().split()[-1] if result.returncode == 0 else "?"
                except Exception:
                    version = "?"

        if installed and not is_installed:
            continue
        if available and is_installed:
            continue

        table.add_row(tool_id, tool["name"], tool["language"], tool["source"], "✓" if is_installed else "", version)

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
    import tarfile
    import zipfile
    import tempfile
    import urllib.request

    repo = tool["repo"]
    binary = tool["binary"]

    # Get latest release if no version specified
    if not version:
        api_url = f"https://api.github.com/repos/{repo}/releases/latest"
        with urllib.request.urlopen(api_url) as response:  # noqa: S310
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
        with urllib.request.urlopen(api_url) as response:  # noqa: S310
            import json

            data = json.loads(response.read())
    except Exception:
        api_url = f"https://api.github.com/repos/{repo}/releases/tags/{version}"
        with urllib.request.urlopen(api_url) as response:  # noqa: S310
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
        urllib.request.urlretrieve(download_url, archive_path)  # noqa: S310

        # Extract
        if download_url.endswith(".tar.gz") or download_url.endswith(".tgz"):
            with tarfile.open(archive_path, "r:gz") as tar:
                tar.extractall(tmppath)  # noqa: S202
        elif download_url.endswith(".zip"):
            with zipfile.ZipFile(archive_path, "r") as z:
                z.extractall(tmppath)  # noqa: S202
        else:
            # Assume it's a raw binary
            shutil.copy(archive_path, install_dir / binary)
            os.chmod(install_dir / binary, 0o755)  # noqa: S103
            return

        # Find the binary in extracted files
        for f in tmppath.rglob("*"):
            if f.is_file() and f.name == binary:
                shutil.copy(f, install_dir / binary)
                os.chmod(install_dir / binary, 0o755)  # noqa: S103
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
    script = """#!/usr/bin/env bash
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
"""

    if output:
        with open(output, "w") as f:
            f.write(script)
        os.chmod(output, 0o755)  # noqa: S103
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
            result = subprocess.run(cmd.split(), capture_output=True, text=True, timeout=5)
            if result.returncode == 0:
                version = result.stdout.strip().split()[-1]
                console.print(f"  [green]✓[/green] {name}: {version}")
            else:
                console.print(f"  [yellow]![/yellow] {name}: not found (optional)")
        except Exception:
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
        console.print(f'  Add to your shell config: export PATH="{install_dir}:$PATH"')


# ============================================================================
# IDE / Browser / AI App Integration
# ============================================================================

# MCP config paths for various apps
MCP_CONFIG_PATHS = {
    "claude": {
        "macos": "~/Library/Application Support/Claude/claude_desktop_config.json",
        "linux": "~/.config/claude/claude_desktop_config.json",
        "windows": "%APPDATA%/Claude/claude_desktop_config.json",
    },
    "vscode": {
        "macos": "~/Library/Application Support/Code/User/globalStorage/saoudrizwan.claude-dev/settings/cline_mcp_settings.json",
        "linux": "~/.config/Code/User/globalStorage/saoudrizwan.claude-dev/settings/cline_mcp_settings.json",
        "windows": "%APPDATA%/Code/User/globalStorage/saoudrizwan.claude-dev/settings/cline_mcp_settings.json",
    },
    "cursor": {
        "macos": "~/Library/Application Support/Cursor/User/globalStorage/saoudrizwan.claude-dev/settings/cline_mcp_settings.json",
        "linux": "~/.config/Cursor/User/globalStorage/saoudrizwan.claude-dev/settings/cline_mcp_settings.json",
        "windows": "%APPDATA%/Cursor/User/globalStorage/saoudrizwan.claude-dev/settings/cline_mcp_settings.json",
    },
    "antigravity": {
        "macos": "~/.gemini/antigravity/mcp_config.json",
        "linux": "~/.gemini/antigravity/mcp_config.json",
        "windows": "%USERPROFILE%/.gemini/antigravity/mcp_config.json",
    },
    "copilot": {
        "macos": "~/.copilot/mcp-config.json",
        "linux": "~/.copilot/mcp-config.json",
        "windows": "%USERPROFILE%/.copilot/mcp-config.json",
    },
    "jan": {
        "macos": "~/Library/Application Support/Jan/data/mcp_config.json",
        "linux": "~/.config/jan/data/mcp_config.json",
        "windows": "%APPDATA%/Jan/data/mcp_config.json",
    },
    "trae": {
        "macos": "~/Library/Application Support/Trae/User/mcp.json",
        "linux": "~/.config/Trae/User/mcp.json",
        "windows": "%APPDATA%/Trae/User/mcp.json",
    },
    "5ire": {
        "macos": "~/Library/Application Support/5ire/mcp.json",
        "linux": "~/.config/5ire/mcp.json",
        "windows": "%APPDATA%/5ire/mcp.json",
    },
}


def get_mcp_config_path(app: str) -> Optional[Path]:
    """Get MCP config path for an app."""
    if app not in MCP_CONFIG_PATHS:
        return None

    system = platform.system().lower()
    os_key = {"darwin": "macos", "linux": "linux", "windows": "windows"}.get(system)
    if not os_key:
        return None

    path_str = MCP_CONFIG_PATHS[app].get(os_key)
    if not path_str:
        return None

    return Path(os.path.expandvars(os.path.expanduser(path_str)))


def get_mcp_server_config() -> dict:
    """Get hanzo-mcp server configuration for MCP config files."""
    return {"command": "uvx", "args": ["--upgrade", "hanzo-mcp@latest"], "env": {}}


@install_group.command(name="ide")
@click.argument("target", required=False)
@click.option("--all", "install_all", is_flag=True, help="Install to all detected IDEs")
@click.option("--list", "list_only", is_flag=True, help="List available IDEs")
def install_ide(target: str, install_all: bool, list_only: bool):
    """Install Hanzo MCP to IDEs (VS Code, Cursor, Antigravity, etc.).

    \b
    Examples:
      hanzo install ide              # List detected IDEs
      hanzo install ide claude       # Install to Claude Desktop
      hanzo install ide vscode       # Install to VS Code
      hanzo install ide --all        # Install to all detected IDEs

    \b
    Supported IDEs:
      claude       - Claude Desktop
      vscode       - Visual Studio Code (via Cline extension)
      cursor       - Cursor IDE (via Cline extension)
      antigravity  - Antigravity IDE (VS Code based)
      copilot      - GitHub Copilot
      jan          - Jan AI
      trae         - Trae IDE
      5ire         - 5ire AI
    """
    import json

    if list_only or (not target and not install_all):
        # List detected IDEs
        console.print("[bold]Detected IDEs with MCP support:[/bold]")
        console.print()

        for app_name in MCP_CONFIG_PATHS:
            config_path = get_mcp_config_path(app_name)
            if config_path:
                exists = config_path.exists()
                parent_exists = config_path.parent.exists()

                if exists:
                    # Check if hanzo-mcp already configured
                    try:
                        with open(config_path) as f:
                            config = json.load(f)
                        has_hanzo = "hanzo" in config.get("mcpServers", {}) or "hanzo-mcp" in config.get(
                            "mcpServers", {}
                        )
                        status = (
                            "[green]✓ hanzo-mcp configured[/green]" if has_hanzo else "[yellow]○ no hanzo-mcp[/yellow]"
                        )
                    except Exception:
                        status = "[dim]○ config exists[/dim]"
                    console.print(f"  [green]✓[/green] {app_name}: {status}")
                elif parent_exists:
                    console.print(f"  [yellow]○[/yellow] {app_name}: [dim]app installed, no MCP config[/dim]")
                else:
                    console.print(f"  [dim]○[/dim] {app_name}: [dim]not installed[/dim]")

        console.print()
        console.print("[dim]Run: hanzo install ide <name> to configure[/dim]")
        return

    targets = list(MCP_CONFIG_PATHS.keys()) if install_all else [target]

    for app in targets:
        if app not in MCP_CONFIG_PATHS:
            console.print(f"[red]Unknown IDE: {app}[/red]")
            console.print(f"Available: {', '.join(MCP_CONFIG_PATHS.keys())}")
            continue

        config_path = get_mcp_config_path(app)
        if not config_path:
            console.print(f"[yellow]![/yellow] {app}: not supported on this platform")
            continue

        console.print(f"[cyan]Configuring {app}...[/cyan]")

        # Create parent directory if needed
        config_path.parent.mkdir(parents=True, exist_ok=True)

        # Load or create config
        if config_path.exists():
            try:
                with open(config_path) as f:
                    config = json.load(f)
            except json.JSONDecodeError:
                config = {}
        else:
            config = {}

        # Ensure mcpServers key exists
        if "mcpServers" not in config:
            config["mcpServers"] = {}

        # Add hanzo-mcp server
        config["mcpServers"]["hanzo"] = get_mcp_server_config()

        # Write config
        with open(config_path, "w") as f:
            json.dump(config, f, indent=2)

        console.print(f"  [green]✓[/green] {app} configured: {config_path}")

    console.print()
    console.print("[bold green]✓[/bold green] MCP configuration complete")
    console.print("[dim]Restart your IDE to load hanzo-mcp[/dim]")


@install_group.command(name="browser")
@click.argument("browser", required=False)
@click.option("--list", "list_only", is_flag=True, help="List browser extension install URLs")
def install_browser(browser: str, list_only: bool):
    """Install Hanzo browser extension.

    \b
    Examples:
      hanzo install browser          # List browser extension links
      hanzo install browser chrome   # Open Chrome Web Store
      hanzo install browser firefox  # Open Firefox Add-ons

    \b
    Supported browsers:
      chrome   - Google Chrome / Chromium
      firefox  - Mozilla Firefox
      safari   - Apple Safari
      edge     - Microsoft Edge
    """
    import webbrowser

    extension_urls = {
        "chrome": "https://chrome.google.com/webstore/detail/hanzo-ai/placeholder",
        "firefox": "https://addons.mozilla.org/en-US/firefox/addon/hanzo-ai/",
        "safari": "https://apps.apple.com/app/hanzo-ai/placeholder",
        "edge": "https://microsoftedge.microsoft.com/addons/detail/hanzo-ai/placeholder",
    }

    # Dev install instructions
    dev_instructions = {
        "chrome": "chrome://extensions → Enable Developer Mode → Load unpacked → Select extension folder",
        "firefox": "about:debugging → This Firefox → Load Temporary Add-on → Select manifest.json",
        "safari": "Safari → Preferences → Advanced → Enable Develop menu → Develop → Allow Unsigned Extensions",
        "edge": "edge://extensions → Enable Developer Mode → Load unpacked → Select extension folder",
    }

    if list_only or not browser:
        console.print("[bold]Hanzo Browser Extension[/bold]")
        console.print()

        # Check which browsers are available
        browsers_found = []

        # macOS browser detection
        if platform.system() == "Darwin":
            browser_paths = {
                "chrome": "/Applications/Google Chrome.app",
                "firefox": "/Applications/Firefox.app",
                "safari": "/Applications/Safari.app",
                "edge": "/Applications/Microsoft Edge.app",
            }
            for name, path in browser_paths.items():
                if Path(path).exists():
                    browsers_found.append(name)

        console.print("[cyan]Install from store (recommended):[/cyan]")
        for name, url in extension_urls.items():
            detected = " [green](detected)[/green]" if name in browsers_found else ""
            console.print(f"  {name}: {url}{detected}")

        console.print()
        console.print("[cyan]Developer install (for testing):[/cyan]")
        for name, instruction in dev_instructions.items():
            console.print(f"  {name}:")
            console.print(f"    {instruction}")

        console.print()
        console.print("[dim]Extension source: ~/work/hanzo/extension[/dim]")
        return

    if browser.lower() not in extension_urls:
        console.print(f"[red]Unknown browser: {browser}[/red]")
        console.print(f"Available: {', '.join(extension_urls.keys())}")
        return

    url = extension_urls[browser.lower()]
    console.print(f"[cyan]Opening {browser} extension page...[/cyan]")
    webbrowser.open(url)
    console.print(f"[green]✓[/green] Opened: {url}")


@install_group.command(name="ai")
@click.argument("app", required=False)
@click.option("--list", "list_only", is_flag=True, help="List AI apps")
def install_ai(app: str, list_only: bool):
    """Configure Hanzo MCP for AI apps (Claude Desktop, Jan, etc.).

    This is an alias for 'hanzo install ide' focused on AI applications.

    \b
    Examples:
      hanzo install ai               # List AI apps
      hanzo install ai claude        # Configure Claude Desktop
      hanzo install ai jan           # Configure Jan AI
    """
    # Delegate to install_ide
    from click import Context

    ctx = Context(install_ide)
    ctx.invoke(install_ide, target=app, install_all=False, list_only=list_only or not app)


@install_group.command(name="all")
@click.option("--force", "-f", is_flag=True, help="Force reinstall")
def install_all_cmd(force: bool):
    """Install everything: tools + IDE integrations + browser extension info.

    \b
    This command:
      1. Installs all Python tools (cli, mcp, agents)
      2. Configures all detected IDEs with hanzo-mcp
      3. Shows browser extension installation instructions
    """
    console.print(
        Panel.fit(
            "[bold cyan]Hanzo Full Installation[/bold cyan]\n"
            "[dim]Installing tools, IDE integrations, and browser extension[/dim]",
            border_style="cyan",
        )
    )
    console.print()

    # 1. Install Python tools
    console.print("[bold]1. Installing CLI Tools[/bold]")
    from click import Context

    for tool_id in ["cli", "mcp", "agents"]:
        _install_single_tool(tool_id, None, False, force)

    console.print()

    # 2. Configure all detected IDEs
    console.print("[bold]2. Configuring IDE Integrations[/bold]")
    import json

    configured = []
    for app_name in MCP_CONFIG_PATHS:
        config_path = get_mcp_config_path(app_name)
        if config_path and config_path.parent.exists():
            # Create or update config
            config_path.parent.mkdir(parents=True, exist_ok=True)

            if config_path.exists():
                try:
                    with open(config_path) as f:
                        config = json.load(f)
                except Exception:
                    config = {}
            else:
                config = {}

            if "mcpServers" not in config:
                config["mcpServers"] = {}

            config["mcpServers"]["hanzo"] = get_mcp_server_config()

            with open(config_path, "w") as f:
                json.dump(config, f, indent=2)

            configured.append(app_name)
            console.print(f"  [green]✓[/green] {app_name}")

    if not configured:
        console.print("  [dim](no IDEs detected)[/dim]")

    console.print()

    # 3. Browser extension info
    console.print("[bold]3. Browser Extension[/bold]")
    console.print("  Install from: https://chrome.google.com/webstore/detail/hanzo-ai/")
    console.print("  Or load unpacked from: ~/work/hanzo/extension")

    console.print()
    console.print("[bold green]✓[/bold green] Full installation complete!")
    console.print()
    console.print("[dim]Next steps:[/dim]")
    console.print("  1. Restart your IDEs to load hanzo-mcp")
    console.print("  2. Install browser extension (optional)")
    console.print("  3. Run: hanzo doctor  # to verify installation")


# ============================================================================
# Nanobrowser - Lightweight Agent Browser
# ============================================================================

NANOBROWSER_PATH = Path.home() / "work" / "nanobrowser" / "nanobrowser"


@install_group.command(name="nanobrowser")
@click.option("--build", "-b", is_flag=True, help="Build from source")
@click.option("--dev", is_flag=True, help="Run in development mode")
@click.option("--open", "open_browser", is_flag=True, help="Open Chrome with extension loaded")
def install_nanobrowser(build: bool, dev: bool, open_browser: bool):
    """Install/build Nanobrowser - lightweight AI browser for agents.

    \b
    Nanobrowser is a Chrome extension for AI web automation.
    It provides a multi-agent system (Planner + Navigator) that
    can browse the web autonomously using LLMs.

    \b
    Examples:
      hanzo install nanobrowser           # Check status
      hanzo install nanobrowser --build   # Build from source
      hanzo install nanobrowser --dev     # Run dev server
      hanzo install nanobrowser --open    # Load in Chrome

    \b
    LLM Support:
      - OpenAI (GPT-4, GPT-4o)
      - Anthropic (Claude Sonnet, Haiku)
      - Google (Gemini)
      - Ollama (local models)
      - Groq, Cerebras, Llama
    """
    nanobrowser_dir = NANOBROWSER_PATH

    if not nanobrowser_dir.exists():
        console.print("[red]Nanobrowser not found[/red]")
        console.print(f"Expected at: {nanobrowser_dir}")
        console.print()
        console.print("Clone it with:")
        console.print(f"  git clone https://github.com/nanobrowser/nanobrowser {nanobrowser_dir}")
        return

    dist_dir = nanobrowser_dir / "dist"

    if build or dev:
        console.print("[cyan]Building Nanobrowser...[/cyan]")

        # Install dependencies
        console.print("  Installing dependencies...")
        result = subprocess.run(["pnpm", "install"], cwd=str(nanobrowser_dir), capture_output=True, text=True)
        if result.returncode != 0:
            console.print(f"[red]Failed to install dependencies: {result.stderr}[/red]")
            return

        if dev:
            console.print("  Starting dev server...")
            console.print("[dim]Press Ctrl+C to stop[/dim]")
            subprocess.run(["pnpm", "dev"], cwd=str(nanobrowser_dir))
        else:
            console.print("  Building extension...")
            result = subprocess.run(["pnpm", "build"], cwd=str(nanobrowser_dir), capture_output=True, text=True)
            if result.returncode != 0:
                console.print(f"[red]Build failed: {result.stderr}[/red]")
                return
            console.print(f"[green]✓[/green] Built to: {dist_dir}")

    elif open_browser:
        if not dist_dir.exists():
            console.print("[yellow]Extension not built yet. Run with --build first.[/yellow]")
            return

        # Open Chrome with extension loaded (macOS)
        if platform.system() == "Darwin":
            chrome_path = "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"
            if not Path(chrome_path).exists():
                console.print("[red]Chrome not found at default location[/red]")
                return

            console.print("[cyan]Opening Chrome with Nanobrowser extension...[/cyan]")
            subprocess.Popen(
                [
                    chrome_path,
                    f"--load-extension={dist_dir}",
                    "--new-window",
                ]
            )
            console.print("[green]✓[/green] Chrome launched with Nanobrowser")
        else:
            console.print("[yellow]Auto-open not supported on this platform[/yellow]")
            console.print(f"Manually load the extension from: {dist_dir}")

    else:
        # Status check
        console.print("[bold]Nanobrowser Status[/bold]")
        console.print(f"  Location: {nanobrowser_dir}")
        console.print(f"  Built: {'[green]✓[/green]' if dist_dir.exists() else '[yellow]○[/yellow] (run --build)'}")

        # Get version from package.json
        package_json = nanobrowser_dir / "package.json"
        if package_json.exists():
            import json

            with open(package_json) as f:
                pkg = json.load(f)
            console.print(f"  Version: {pkg.get('version', 'unknown')}")

        console.print()
        console.print("[cyan]Installation Steps:[/cyan]")
        console.print("  1. Build: hanzo install nanobrowser --build")
        console.print("  2. Open Chrome: chrome://extensions")
        console.print("  3. Enable 'Developer mode'")
        console.print("  4. Click 'Load unpacked'")
        console.print(f"  5. Select: {dist_dir}")
        console.print()
        console.print("[cyan]Or auto-load:[/cyan]")
        console.print("  hanzo install nanobrowser --open")


# ============================================================================
# Runtime - Sandboxed Agent Execution Environment
# ============================================================================

RUNTIME_PATH = Path.home() / "work" / "hanzo" / "runtime"


@install_group.command(name="runtime")
@click.option("--setup", "-s", is_flag=True, help="Set up the runtime environment")
@click.option("--sdk", type=click.Choice(["python", "typescript", "both"]), help="Install SDK")
@click.option("--computer-use", is_flag=True, help="Set up VNC desktop for computer use")
def install_runtime(setup: bool, sdk: str, computer_use: bool):
    """Configure Hanzo Runtime - sandboxed agent execution.

    \b
    The Hanzo Runtime provides:
    - Sub-90ms sandbox creation
    - Isolated code execution for AI-generated code
    - Computer Use (VNC desktop control)
    - File, Git, LSP, and Execute APIs
    - OCI/Docker compatibility

    \b
    Examples:
      hanzo install runtime              # Check status
      hanzo install runtime --setup      # Initialize runtime
      hanzo install runtime --sdk python # Install Python SDK
      hanzo install runtime --computer-use # Set up desktop control

    \b
    SDKs:
      pip install hanzo-runtime      # Python
      npm install @hanzo/runtime     # TypeScript
    """
    runtime_dir = RUNTIME_PATH

    if sdk:
        console.print(f"[cyan]Installing Runtime SDK ({sdk})...[/cyan]")

        if sdk in ("python", "both"):
            if shutil.which("uv"):
                subprocess.run(["uv", "pip", "install", "hanzo-runtime"], check=True)
            else:
                subprocess.run([sys.executable, "-m", "pip", "install", "hanzo-runtime"], check=True)
            console.print("[green]✓[/green] Python SDK installed")

        if sdk in ("typescript", "both"):
            subprocess.run(["npm", "install", "-g", "@hanzo/runtime"], check=True)
            console.print("[green]✓[/green] TypeScript SDK installed")

        return

    if computer_use:
        console.print("[cyan]Setting up Computer Use environment...[/cyan]")
        console.print()

        # Check Docker
        if not shutil.which("docker"):
            console.print("[red]Docker is required for Computer Use[/red]")
            console.print("Install: https://docs.docker.com/get-docker/")
            return

        # Show Dockerfile info
        dockerfile_path = runtime_dir / "hack" / "computer-use" / "Dockerfile"
        if dockerfile_path.exists():
            console.print("[green]✓[/green] Computer Use Dockerfile found")
            console.print(f"  Path: {dockerfile_path}")
        else:
            console.print("[yellow]![/yellow] Dockerfile not found")

        console.print()
        console.print("[cyan]Computer Use provides:[/cyan]")
        console.print("  - Xvfb (virtual display)")
        console.print("  - XFCE4 desktop environment")
        console.print("  - x11vnc (VNC server on port 5901)")
        console.print("  - noVNC (web access on port 6901)")
        console.print("  - xdotool, xautomation (mouse/keyboard)")
        console.print("  - Chromium browser")
        console.print()
        console.print("[cyan]Build and run:[/cyan]")
        console.print(f"  cd {runtime_dir / 'hack' / 'computer-use'}")
        console.print("  docker build -t hanzo-computer-use .")
        console.print("  docker run -p 5901:5901 -p 6901:6901 hanzo-computer-use")
        console.print()
        console.print("Then access: http://localhost:6901 (noVNC web client)")
        return

    if setup:
        console.print("[cyan]Setting up Hanzo Runtime...[/cyan]")

        if not runtime_dir.exists():
            console.print(f"[red]Runtime not found at: {runtime_dir}[/red]")
            return

        # Build Go binaries
        console.print("  Building CLI...")
        cli_dir = runtime_dir / "apps" / "cli"
        if cli_dir.exists():
            result = subprocess.run(
                ["go", "build", "-o", str(Path.home() / ".hanzo" / "bin" / "hanzo-runtime"), "."],
                cwd=str(cli_dir),
                capture_output=True,
                text=True,
            )
            if result.returncode == 0:
                console.print("[green]✓[/green] CLI built")
            else:
                console.print(f"[yellow]![/yellow] CLI build failed: {result.stderr}")

        return

    # Status check
    console.print("[bold]Hanzo Runtime Status[/bold]")

    if runtime_dir.exists():
        console.print(f"  [green]✓[/green] Source: {runtime_dir}")

        # Check components
        components = {
            "CLI": runtime_dir / "apps" / "cli",
            "Daemon": runtime_dir / "apps" / "daemon",
            "Runner": runtime_dir / "apps" / "runner",
            "Python SDK": runtime_dir / "libs" / "sdk-python",
            "TypeScript SDK": runtime_dir / "libs" / "sdk-typescript",
            "Computer Use": runtime_dir / "libs" / "computer-use",
        }

        console.print()
        console.print("[cyan]Components:[/cyan]")
        for name, path in components.items():
            status = "[green]✓[/green]" if path.exists() else "[dim]○[/dim]"
            console.print(f"  {status} {name}")

        # Check SDKs installed
        console.print()
        console.print("[cyan]Installed SDKs:[/cyan]")

        # Python SDK
        try:
            result = subprocess.run(
                [sys.executable, "-c", "import hanzo_runtime; print(hanzo_runtime.__version__)"],
                capture_output=True,
                text=True,
            )
            if result.returncode == 0:
                console.print(f"  [green]✓[/green] Python: {result.stdout.strip()}")
            else:
                console.print("  [dim]○[/dim] Python: not installed")
        except Exception:
            console.print("  [dim]○[/dim] Python: not installed")

        # TypeScript SDK
        result = subprocess.run(["npm", "list", "-g", "@hanzo/runtime"], capture_output=True, text=True)
        if "@hanzo/runtime" in result.stdout:
            console.print(f"  [green]✓[/green] TypeScript: installed")
        else:
            console.print("  [dim]○[/dim] TypeScript: not installed")

    else:
        console.print(f"  [red]○[/red] Not found: {runtime_dir}")

    console.print()
    console.print("[dim]Install SDKs:[/dim]")
    console.print("  pip install hanzo-runtime")
    console.print("  npm install @hanzo/runtime")


# ============================================================================
# Cas Infrastructure (Casdoor, Casibase, Casvisor)
# ============================================================================

CAS_PATH = Path.home() / "work" / "cas"


@install_group.command(name="cas")
@click.argument("component", required=False)
@click.option("--setup", "-s", is_flag=True, help="Set up the component")
@click.option("--start", is_flag=True, help="Start the service")
def install_cas(component: str, setup: bool, start: bool):
    """Configure Cas infrastructure (auth, AI platform, VM management).

    \b
    Components:
      casdoor   - Authentication/IAM system (Single Sign-On)
      casibase  - AI Cloud OS with MCP/A2A support
      casvisor  - Cloud operating system (VM/machine management)

    \b
    Examples:
      hanzo install cas                   # Check status
      hanzo install cas casdoor --setup   # Set up Casdoor
      hanzo install cas casibase --start  # Start Casibase

    \b
    Casibase Features:
      - AI knowledge base management
      - MCP (Model Context Protocol) server
      - A2A (Agent-to-Agent) management
      - Supports ChatGPT, Claude, Llama, Ollama, etc.
    """
    cas_dir = CAS_PATH

    components_info = {
        "casdoor": {
            "name": "Casdoor",
            "description": "Authentication/IAM - Single Sign-On",
            "path": cas_dir / "casdoor",
            "port": 8000,
            "docs": "https://casdoor.org",
        },
        "casibase": {
            "name": "Casibase",
            "description": "AI Cloud OS - Knowledge base + MCP/A2A",
            "path": cas_dir / "casibase",
            "port": 14000,
            "docs": "https://casibase.org",
        },
        "casvisor": {
            "name": "Casvisor",
            "description": "Cloud OS - VM/Machine management",
            "path": cas_dir / "casvisor",
            "port": 16001,
            "docs": "https://casvisor.org",
        },
    }

    if component:
        if component not in components_info:
            console.print(f"[red]Unknown component: {component}[/red]")
            console.print(f"Available: {', '.join(components_info.keys())}")
            return

        info = components_info[component]
        comp_path = info["path"]

        if not comp_path.exists():
            console.print(f"[red]{info['name']} not found at: {comp_path}[/red]")
            console.print(f"Clone: git clone https://github.com/{component}/{component} {comp_path}")
            return

        if setup:
            console.print(f"[cyan]Setting up {info['name']}...[/cyan]")
            console.print()

            # Check for Go
            if not shutil.which("go"):
                console.print("[red]Go is required[/red]")
                console.print("Install: https://go.dev/dl/")
                return

            # Build
            console.print("  Building...")
            result = subprocess.run(["go", "build", "."], cwd=str(comp_path), capture_output=True, text=True)
            if result.returncode == 0:
                console.print(f"[green]✓[/green] {info['name']} built")
            else:
                console.print(f"[red]Build failed: {result.stderr}[/red]")
                return

            # Frontend
            web_dir = comp_path / "web"
            if web_dir.exists():
                console.print("  Building frontend...")
                subprocess.run(["yarn", "install"], cwd=str(web_dir), check=False)
                subprocess.run(["yarn", "build"], cwd=str(web_dir), check=False)

            console.print()
            console.print(f"[green]✓[/green] {info['name']} setup complete")
            console.print(f"Run: cd {comp_path} && ./{component}")

        elif start:
            console.print(f"[cyan]Starting {info['name']}...[/cyan]")
            binary = comp_path / component
            if not binary.exists():
                console.print(f"[yellow]Not built. Run with --setup first.[/yellow]")
                return
            subprocess.Popen([str(binary)], cwd=str(comp_path))
            console.print(f"[green]✓[/green] Started on port {info['port']}")
            console.print(f"  Open: http://localhost:{info['port']}")

        else:
            console.print(f"[bold]{info['name']}[/bold]")
            console.print(f"  Description: {info['description']}")
            console.print(f"  Path: {comp_path}")
            console.print(f"  Port: {info['port']}")
            console.print(f"  Docs: {info['docs']}")

    else:
        # Status check
        console.print("[bold]Cas Infrastructure[/bold]")
        console.print()

        for comp_id, info in components_info.items():
            path = info["path"]
            exists = path.exists()
            binary = path / comp_id if exists else None
            built = binary and binary.exists() if binary else False

            status = "[green]✓[/green]" if exists else "[dim]○[/dim]"
            build_status = " [green](built)[/green]" if built else " [yellow](not built)[/yellow]" if exists else ""

            console.print(f"  {status} {info['name']}: {info['description']}{build_status}")

        console.print()
        console.print("[dim]Set up a component: hanzo install cas <component> --setup[/dim]")
