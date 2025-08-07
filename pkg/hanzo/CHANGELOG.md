# Changelog

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