#!/usr/bin/env bash

# Comprehensive script to publish all Python packages to PyPI
# Usage: ./bin/publish-all-packages.sh [package-name]
# If no package name is provided, all packages will be published

set -e  # Exit on error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Function to print colored output
print_info() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

print_warn() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Check if PYPI_TOKEN is set
if [ -z "$PYPI_TOKEN" ]; then
    print_error "PYPI_TOKEN environment variable is not set"
    exit 1
fi

# Get the package to publish (if specified)
SPECIFIC_PACKAGE=$1

# List of all packages in order of dependency
PACKAGES=(
    "hanzo-network"
    "hanzo-memory"
    "hanzo-agents"
    "hanzo-aci"
    "hanzo-mcp"
    "hanzo-repl"
    "hanzo"
)

# Function to get package version from pyproject.toml
get_version() {
    local package=$1
    local pyproject="pkg/$package/pyproject.toml"
    if [ -f "$pyproject" ]; then
        grep "^version = " "$pyproject" | sed 's/version = "\(.*\)"/\1/'
    else
        echo "unknown"
    fi
}

# Function to check if package exists on PyPI
check_pypi() {
    local package=$1
    local version=$2
    curl -s "https://pypi.org/pypi/$package/$version/json" > /dev/null 2>&1
    return $?
}

# Function to build and publish a package
publish_package() {
    local package=$1
    local package_dir="pkg/$package"
    
    if [ ! -d "$package_dir" ]; then
        print_error "Package directory $package_dir does not exist"
        return 1
    fi
    
    print_info "Processing package: $package"
    
    # Get version
    local version=$(get_version "$package")
    print_info "Package version: $version"
    
    # Check if already published
    if check_pypi "$package" "$version"; then
        print_warn "Package $package version $version already exists on PyPI, skipping..."
        return 0
    fi
    
    cd "$package_dir"
    
    # Clean previous builds
    print_info "Cleaning previous builds..."
    rm -rf dist/ build/ *.egg-info
    
    # Build the package
    print_info "Building package..."
    python -m build
    
    # Upload to PyPI
    print_info "Uploading to PyPI..."
    python -m twine upload dist/* --skip-existing
    
    print_info "✅ Successfully published $package version $version"
    
    cd - > /dev/null
}

# Main execution
main() {
    print_info "Starting package publication process..."
    
    # Install required tools
    print_info "Installing build tools..."
    python -m pip install --quiet --upgrade pip build twine
    
    # If specific package is provided, publish only that
    if [ -n "$SPECIFIC_PACKAGE" ]; then
        if [[ " ${PACKAGES[@]} " =~ " ${SPECIFIC_PACKAGE} " ]]; then
            publish_package "$SPECIFIC_PACKAGE"
        else
            print_error "Unknown package: $SPECIFIC_PACKAGE"
            print_info "Available packages: ${PACKAGES[*]}"
            exit 1
        fi
    else
        # Publish all packages
        print_info "Publishing all packages..."
        for package in "${PACKAGES[@]}"; do
            publish_package "$package" || {
                print_error "Failed to publish $package"
                exit 1
            }
        done
    fi
    
    print_info "🎉 All packages published successfully!"
}

# Run main function
main