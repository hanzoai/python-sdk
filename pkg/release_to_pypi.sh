#!/bin/bash
# Release script for Hanzo Python SDK packages

set -e

echo "🚀 Hanzo Python SDK Release Script"
echo "=================================="

# Check if twine is installed
if ! command -v twine &> /dev/null; then
    echo "❌ twine is not installed. Install with: pip install twine"
    exit 1
fi

# Function to release a package
release_package() {
    local pkg_name=$1
    local pkg_dir=$2
    
    echo ""
    echo "📦 Releasing $pkg_name..."
    echo "----------------------------"
    
    cd "$pkg_dir"
    
    # Check if dist directory exists
    if [ ! -d "dist" ]; then
        echo "❌ No dist directory found for $pkg_name"
        return 1
    fi
    
    # List files to be uploaded
    echo "Files to upload:"
    ls -la dist/
    
    # Upload to PyPI (uncomment when ready)
    # echo "Uploading to PyPI..."
    # python -m twine upload dist/*
    
    # For test PyPI (uncomment to test)
    # python -m twine upload --repository testpypi dist/*
    
    echo "✅ $pkg_name ready for release"
    echo "   To upload, run: python -m twine upload dist/*"
    
    cd ..
}

# Release each package
release_package "hanzo-mcp" "hanzo-mcp"
release_package "hanzo-agents" "hanzo-agents"
release_package "hanzo-network" "hanzo-network"
release_package "hanzo-memory" "hanzo-memory"

echo ""
echo "🎉 Release preparation complete!"
echo ""
echo "Next steps:"
echo "1. Set up PyPI credentials: ~/.pypirc"
echo "2. Test upload to TestPyPI first:"
echo "   python -m twine upload --repository testpypi dist/*"
echo "3. Upload to PyPI:"
echo "   python -m twine upload dist/*"
echo ""
echo "Package versions:"
echo "  - hanzo-mcp v0.7.5"
echo "  - hanzo-agents v0.1.0"
echo "  - hanzo-network v0.1.0"
echo "  - hanzo-memory v1.0.0"