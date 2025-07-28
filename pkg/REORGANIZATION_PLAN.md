# Python SDK Reorganization Plan

## Identified Issues

### 1. Duplicate Packages
- **hanzo_network**: Exists in both `./hanzo-network/` and `./hanzo-mcp/hanzo_network/`
- **hanzo-cli**: Exists in both `./hanzo-cli/` and `./hanzo-mcp/pkg/hanzo-cli/`

### 2. Unclear Package Structure
- `hanzo-cli-wrapper` vs `hanzo-cli` - purpose overlap
- Multiple nested `pkg/` directories

## Recommended Actions

### Phase 1: Remove Duplicates
1. Remove `./hanzo-mcp/hanzo_network/` - use the package version in `./hanzo-network/`
2. Remove `./hanzo-mcp/pkg/hanzo-cli/` - use the main `./hanzo-cli/` package
3. Update all imports in hanzo-mcp to use the package versions

### Phase 2: Clarify Package Structure
1. Merge `hanzo-cli-wrapper` functionality into `hanzo-cli` if they serve the same purpose
2. Move all packages to a consistent location (root level, not nested in hanzo-mcp)

### Phase 3: Update Dependencies
1. Update `hanzo-mcp/pyproject.toml` to reference the correct package locations
2. Ensure all cross-package dependencies use consistent paths

## Commands to Execute

```bash
# Phase 1: Remove duplicates
rm -rf ./hanzo-mcp/hanzo_network/
rm -rf ./hanzo-mcp/pkg/

# Phase 2: Update imports (need to search and replace)
# In hanzo-mcp files, replace:
# from hanzo_network import ... → from hanzo_network import ...
# (No change needed as import path remains the same)

# Phase 3: Update dependencies in pyproject.toml files
# Ensure hanzo-mcp depends on hanzo-network package properly
```

## For Go Consensus Project

The error shows an incorrect import in `chains/atomic/shared_memory.go:7:2`:
```
github.com/luxfi/crypto/database  # This package doesn't exist
```

To fix:
1. Check what the correct database import should be (likely one of):
   - `github.com/luxfi/consensus/database`
   - `github.com/luxfi/luxd/database` 
   - Or check other files in the project for the correct import

2. Update the import in `chains/atomic/shared_memory.go`

3. Run:
   ```bash
   go mod tidy
   make test
   ```