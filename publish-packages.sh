#!/bin/bash
# Script to build and publish updated Hanzo packages to PyPI

set -e

echo "Building and publishing Hanzo Python SDK packages..."

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Function to build and check package
build_package() {
    local pkg_dir=$1
    local pkg_name=$2

    echo -e "${YELLOW}Building $pkg_name...${NC}"
    cd "$pkg_dir"

    # Clean previous builds
    rm -rf dist/ build/ *.egg-info/

    # Build the package
    python -m build

    # Check the built package
    if [ -f dist/*.whl ]; then
        echo -e "${GREEN}✓ Built $pkg_name successfully${NC}"
        ls -la dist/
    else
        echo -e "${RED}✗ Failed to build $pkg_name${NC}"
        return 1
    fi

    cd - > /dev/null
}

# Function to publish package
publish_package() {
    local pkg_dir=$1
    local pkg_name=$2

    echo -e "${YELLOW}Publishing $pkg_name to PyPI...${NC}"
    cd "$pkg_dir"

    # Upload to PyPI (requires authentication)
    # Uncomment when ready to publish:
    # python -m twine upload dist/*

    echo -e "${GREEN}Ready to publish: twine upload dist/*${NC}"

    cd - > /dev/null
}

# Main packages to publish
PACKAGES=(
    "pkg/hanzo-memory:hanzo-memory:1.0.1"
    "pkg/hanzo-mcp:hanzo-mcp:0.8.9"
    "pkg/hanzo-agents:hanzo-agents:0.1.0"
    "pkg/hanzo-network:hanzo-network:0.1.3"
    "pkg/hanzo-aci:hanzo-aci:0.2.8"
    "pkg/hanzo-repl:hanzo-repl:0.1.0"
    "pkg/hanzoai:hanzoai:2.1.0"
)

echo "Packages to build and publish:"
for pkg_info in "${PACKAGES[@]}"; do
    IFS=':' read -r dir name version <<< "$pkg_info"
    echo "  - $name v$version ($dir)"
done
echo

# Build all packages first
echo -e "${YELLOW}Building all packages...${NC}"
for pkg_info in "${PACKAGES[@]}"; do
    IFS=':' read -r dir name version <<< "$pkg_info"
    build_package "$dir" "$name"
done

echo
echo -e "${GREEN}All packages built successfully!${NC}"
echo
echo "To publish to PyPI, run:"
echo "  1. Make sure you have PyPI credentials configured:"
echo "     python -m pip install --upgrade twine"
echo "     python -m twine login"
echo
echo "  2. For each package, run:"
for pkg_info in "${PACKAGES[@]}"; do
    IFS=':' read -r dir name version <<< "$pkg_info"
    echo "     cd $dir && python -m twine upload dist/*"
done
echo
echo "Or uncomment the twine upload line in this script and run again."