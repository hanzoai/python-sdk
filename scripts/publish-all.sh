#!/bin/bash

# Hanzo AI SDK - Complete Package Publishing Script
# Publishes all packages in the monorepo to PyPI

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}====================================${NC}"
echo -e "${BLUE}Hanzo AI SDK - Publishing All Packages${NC}"
echo -e "${BLUE}====================================${NC}"
echo

# Check if we're in the right directory
if [ ! -f "pyproject.toml" ] || [ ! -d "pkg" ]; then
    echo -e "${RED}Error: Must be run from the python-sdk root directory${NC}"
    exit 1
fi

# Check for PYPI_TOKEN
if [ -z "$PYPI_TOKEN" ]; then
    echo -e "${RED}Error: PYPI_TOKEN environment variable not set${NC}"
    echo "Set it with: export PYPI_TOKEN='your-token'"
    exit 1
fi

# Packages to publish (in order)
PACKAGES=("hanzoai" "hanzo" "hanzo-mcp" "hanzo-memory" "hanzo-network" "hanzo-agents" "hanzo-repl")

echo -e "${YELLOW}Packages to publish:${NC}"
for pkg in "${PACKAGES[@]}"; do
    echo -e "  • $pkg"
done
echo

# Function to publish a package
publish_package() {
    local pkg_name=$1
    local pkg_dir=""
    
    # Find package directory
    if [ -f "pyproject.toml" ] && grep -q "name = \"$pkg_name\"" pyproject.toml; then
        pkg_dir="."
    elif [ -d "pkg/$pkg_name" ] && [ -f "pkg/$pkg_name/pyproject.toml" ]; then
        pkg_dir="pkg/$pkg_name"
    else
        echo -e "${YELLOW}Skipping $pkg_name - not found${NC}"
        return 0
    fi
    
    echo -e "${BLUE}Publishing $pkg_name...${NC}"
    
    # Clean previous builds
    rm -rf "$pkg_dir/dist/" "$pkg_dir/build/" "$pkg_dir"/*.egg-info 2>/dev/null || true
    
    # Build package
    (cd "$pkg_dir" && python -m build)
    
    # Upload to PyPI
    (cd "$pkg_dir" && python -m twine upload --username __token__ --password "$PYPI_TOKEN" dist/*)
    
    echo -e "${GREEN}✓ $pkg_name published successfully${NC}"
    echo
}

# Publish each package
for pkg in "${PACKAGES[@]}"; do
    publish_package "$pkg"
done

echo -e "${GREEN}====================================${NC}"
echo -e "${GREEN}All packages published successfully!${NC}"
echo -e "${GREEN}====================================${NC}"
echo
echo "Install with:"
echo -e "${YELLOW}  pip install hanzo[all]        # Complete ecosystem${NC}"
echo -e "${YELLOW}  pip install hanzoai          # AI client library${NC}"
echo -e "${YELLOW}  pip install hanzo-mcp        # MCP development tools${NC}"
echo