#!/bin/bash

# Hanzo AI SDK - Single Package Publishing Script
# Usage: ./scripts/publish-single.sh package-name

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

if [ $# -eq 0 ]; then
    echo -e "${RED}Usage: $0 <package-name>${NC}"
    echo "Available packages:"
    echo "  • hanzoai (main AI client)"
    echo "  • hanzo (CLI and network)"
    echo "  • hanzo-mcp (MCP tools)"
    echo "  • hanzo-memory (memory systems)"
    echo "  • hanzo-network (distributed compute)"
    echo "  • hanzo-agents (multi-agent workflows)"
    echo "  • hanzo-repl (interactive REPL)"
    exit 1
fi

PKG_NAME=$1

echo -e "${BLUE}====================================${NC}"
echo -e "${BLUE}Publishing $PKG_NAME${NC}"
echo -e "${BLUE}====================================${NC}"
echo

# Check for PYPI_TOKEN
if [ -z "$PYPI_TOKEN" ]; then
    echo -e "${RED}Error: PYPI_TOKEN environment variable not set${NC}"
    echo "Set it with: export PYPI_TOKEN='your-token'"
    exit 1
fi

# Find package directory
PKG_DIR=""
if [ -f "pyproject.toml" ] && grep -q "name = \"$PKG_NAME\"" pyproject.toml; then
    PKG_DIR="."
elif [ -d "pkg/$PKG_NAME" ] && [ -f "pkg/$PKG_NAME/pyproject.toml" ]; then
    PKG_DIR="pkg/$PKG_NAME"
else
    echo -e "${RED}Error: Package $PKG_NAME not found${NC}"
    exit 1
fi

echo -e "${YELLOW}Package directory: $PKG_DIR${NC}"

# Get current version
VERSION=$(cd "$PKG_DIR" && python -c "import tomllib; print(tomllib.load(open('pyproject.toml', 'rb'))['project']['version'])")
echo -e "${YELLOW}Current version: $VERSION${NC}"
echo

# Clean previous builds
echo "Cleaning previous builds..."
rm -rf "$PKG_DIR/dist/" "$PKG_DIR/build/" "$PKG_DIR"/*.egg-info 2>/dev/null || true

# Build package
echo "Building package..."
(cd "$PKG_DIR" && python -m build)

# Show built files
echo "Built files:"
ls -la "$PKG_DIR/dist/"
echo

# Upload to PyPI
echo "Uploading to PyPI..."
(cd "$PKG_DIR" && python -m twine upload --username __token__ --password "$PYPI_TOKEN" dist/*)

echo
echo -e "${GREEN}====================================${NC}"
echo -e "${GREEN}$PKG_NAME $VERSION published successfully!${NC}"
echo -e "${GREEN}====================================${NC}"
echo
echo -e "${YELLOW}Install with: pip install $PKG_NAME${NC}"
echo