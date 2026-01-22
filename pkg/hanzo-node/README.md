# hanzo-node

Cross-platform installer for the Hanzo AI node (Rust binary).

## Installation

```bash
# Install via uv
uv tool install hanzo-node

# Or via pip
pip install hanzo-node
```

## Usage

```bash
# Install the node binary
hanzo-node install

# Check status
hanzo-node status

# Upgrade to latest
hanzo-node upgrade

# Run the node (passes args to binary)
hanzo-node run --help

# Uninstall
hanzo-node uninstall
```

## How It Works

This Python package is a thin wrapper that:

1. Detects your platform (macOS/Linux/Windows, x64/arm64)
2. Downloads the appropriate Rust binary from GitHub releases
3. Installs it to `~/.local/bin` (or `%LOCALAPPDATA%\hanzo\bin` on Windows)
4. Provides a CLI to manage the installation

The actual `hanzo-node` is written in Rust for performance. This package just handles cross-platform distribution.

## Supported Platforms

- macOS (Apple Silicon / Intel)
- Linux (x64 / arm64)
- Windows (x64)

## Environment Variables

- `HANZO_INSTALL_DIR` - Override the installation directory (default: `~/.local/bin`)

## License

Apache 2.0
