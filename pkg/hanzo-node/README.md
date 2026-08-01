# hanzo-node

A Python installer that downloads a `hanzo-node` binary from `hanzoai/node`
release assets.

## Read this first

Two different things are called `hanzo-node`, and this package is not the one
most people want.

**The `hanzo-node` command** is a second name for the Hanzo CLI — a symlink to
the same binary, which the Hanzo Cloud control binary resolves first when it
delegates a verb it does not serve itself. You get it from the CLI installer, and
because it is a symlink it can never drift out of step with `hanzo`:

```bash
curl -fsSL https://hanzo.sh | sh
hanzo-node --version     # same build as `hanzo --version`
```

**This package** installs a separate Rust agent-node binary from the
`hanzoai/node` repository. That repository is private, so its release assets
return 404 to an unauthenticated download and `hanzo-node install` cannot
complete unless you already have access. Nothing here is being removed, but if
you landed on it looking for the `hanzo-node` command, use the installer above.

## Usage

```bash
pip install hanzo-node        # or: uv tool install hanzo-node

hanzo-node install            # fetch the binary for your platform
hanzo-node status
hanzo-node upgrade
hanzo-node run --help         # pass through to the binary
hanzo-node uninstall
```

It detects your platform (macOS/Linux/Windows, x64/arm64), downloads the matching
asset, and installs it to `~/.local/bin` — or `%LOCALAPPDATA%\hanzo\bin` on
Windows. `HANZO_INSTALL_DIR` overrides the destination.

## License

Apache 2.0
