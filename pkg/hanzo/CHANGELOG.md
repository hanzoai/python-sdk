# Changelog

## [0.2.10] - 2024-08-07

### Dependencies
- Updated to hanzo-net v0.1.2

### Improvements in hanzo-net v0.1.2
- Fixed async event loop issues ("coroutine 'main' was never awaited")
- Removed "tinychat" branding - now shows "Hanzo Chat"
- Proper handling when called from existing async context
- Fixed "Cannot run the event loop while another loop is running" error

## [0.2.9] - 2024-08-07

### Fixed
- Fixed `hanzo net` command to properly pass arguments to hanzo-net
- Resolved argparse conflict when importing net module
- Improved handling of command-line arguments for both installed and source versions

## [0.2.8] - 2024-08-07

### Changed
- Main command to run Hanzo Network is now `hanzo net` (was `hanzo node`)
- `hanzo node` remains as an alias for backward compatibility

### Notes
- Use `hanzo net` to start the distributed AI compute node
- Use `hanzo network` for agent network management commands

## [0.2.7] - 2024-08-06

### Major Update
- hanzo-net is now published to PyPI! Install with: `pip install hanzo-net`
- No longer requires local installation from GitHub
- Full remote support for distributed AI compute nodes

### Improvements in hanzo-net v0.1.0 (now on PyPI)
- Changed "Exo Cluster" to "Hanzo Network" branding
- Removed "tinychat" label from Web Chat URL
- New HANZO ASCII art instead of exo branding
- Fixed model import path (resolves "Model type llama not supported" error)
- Fully responsive CLI interface that adapts to terminal width
- Dynamic centering of all UI elements
- Adaptive text formatting for narrow terminals

### hanzo CLI Updates
- Improved dependency checking for hanzo/net
- Better error messages when hanzo/net is not found
- Automatic detection of hanzo/net venv

## [0.2.6] - 2024-08-06

### Added
- Robust dependency checking for hanzo/net integration
- `net_check.py` utility for verifying hanzo/net installation
- Comprehensive tests for node command integration
- CI/CD workflows with GitHub Actions
- Automatic venv detection for hanzo/net

### Improved
- Better error handling with clear installation instructions
- Smart Python executable detection (uses hanzo/net venv when available)
- More informative error messages when dependencies are missing
- Path handling for both installed and source versions of hanzo/net

### Fixed
- Python path issues when running hanzo/net
- Dependency resolution for different Python environments
- Import errors when running from different directories

### Testing
- Added unit tests for node command
- Created standalone test script for quick verification
- Set up automated testing in CI/CD pipeline

## [0.2.5] - 2024-08-06

### Added
- Full integration with hanzo/net for distributed AI compute nodes
- `hanzo node` command now launches hanzo/net instances
- Automatic detection of hanzo/net from installed package or source
- WebUI at http://localhost:52415 and ChatGPT-compatible API endpoint
- Support for model selection via `--models` flag
- Network mode selection (mainnet/testnet/local)

### Changed
- Default port for `hanzo node` changed to 52415 to match hanzo/net
- Network defaults to "local" for easier testing
- Improved compute node startup with better status messages

### Fixed
- Removed double welcome message in interactive mode
- Fixed all import issues after package consolidation
- Corrected chat command execution in REPL mode

## [0.2.4] - 2024-08-06

### Changed
- Consolidated package structure by merging hanzo-cli into main hanzo package
- Removed redundant hanzo-mcp-client package
- Cleaned up package structure from 15 to 8 active packages

### Fixed
- Fixed all relative imports after package consolidation
- Updated CI/CD pipeline for new package structure