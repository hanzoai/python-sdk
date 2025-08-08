#!/bin/bash

# Hanzo AI SDK - Build All Packages Script
# Builds all packages without publishing

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}====================================${NC}"
echo -e "${BLUE}Hanzo AI SDK - Building All Packages${NC}"
echo -e "${BLUE}====================================${NC}"
echo

# Check if we're in the right directory
if [ ! -f "pyproject.toml" ] || [ ! -d "pkg" ]; then
    echo -e "${RED}Error: Must be run from the python-sdk root directory${NC}"
    exit 1
fi

# Packages to build
PACKAGES=("hanzoai" "hanzo" "hanzo-mcp" "hanzo-memory" "hanzo-network" "hanzo-agents" "hanzo-repl")

echo -e "${YELLOW}Packages to build:${NC}"
for pkg in "${PACKAGES[@]}"; do
    echo -e "  • $pkg"
done
echo

# Function to build a package
build_package() {
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
    
    echo -e "${BLUE}Building $pkg_name...${NC}"
    
    # Get version
    local version=$(cd "$pkg_dir" && python -c "import tomllib; print(tomllib.load(open('pyproject.toml', 'rb'))['project']['version'])")
    echo -e "${YELLOW}Version: $version${NC}"
    
    # Clean previous builds
    rm -rf "$pkg_dir/dist/" "$pkg_dir/build/" "$pkg_dir"/*.egg-info 2>/dev/null || true
    
    # Build package
    (cd "$pkg_dir" && python -m build)
    
    # Show built files
    echo "Built files:"
    ls -la "$pkg_dir/dist/" | grep -E '\.(whl|tar\.gz)$' || echo "  No dist files found"
    
    echo -e "${GREEN}✓ $pkg_name built successfully${NC}"
    echo
}

# Build each package
for pkg in "${PACKAGES[@]}"; do
    build_package "$pkg"
done

echo -e "${GREEN}====================================${NC}"
echo -e "${GREEN}All packages built successfully!${NC}"
echo -e "${GREEN}====================================${NC}"
echo
echo "To publish all packages:"
echo -e "${YELLOW}  export PYPI_TOKEN='your-token'${NC}"
echo -e "${YELLOW}  ./scripts/publish-all.sh${NC}"
echo
echo "To publish individual package:"
echo -e "${YELLOW}  ./scripts/publish-single.sh hanzoai${NC}"
echo