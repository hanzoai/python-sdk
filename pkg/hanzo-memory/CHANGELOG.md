# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.1.1] - 2025-07-23

### Fixed
- Fixed type checking errors throughout the codebase
- Fixed Settings initialization in config.py
- Added missing return type annotations
- Fixed FastAPI parameter ordering in endpoints
- Changed error responses from JSONResponse to HTTPException for consistency

### Added
- Added comprehensive test coverage for authentication module
- Added tests for CLI commands
- Added edge case tests for various modules

### Changed
- Improved test coverage from 81% to 86%
- Updated all dependencies to latest versions

## [0.1.0] - 2025-07-23

### Added
- Initial release of Hanzo Memory Service
- FastAPI server with memory and knowledge management APIs
- Model Context Protocol (MCP) server support
- InfinityDB embedded vector database integration
- FastEmbed for local ONNX-based embeddings
- LiteLLM for universal LLM interface
- Authentication support with API keys
- CLI interface for server management
- Comprehensive test suite with pytest