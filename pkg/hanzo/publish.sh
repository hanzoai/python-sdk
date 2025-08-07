#!/bin/bash

# Hanzo Package Publishing Script
# Version 0.2.5

set -e

echo "=================================="
echo "Hanzo Package Publishing"
echo "Version: 0.2.5"
echo "=================================="
echo

# Check if we're in the right directory
if [ ! -f "pyproject.toml" ]; then
    echo "Error: pyproject.toml not found. Please run from pkg/hanzo directory."
    exit 1
fi

# Clean previous builds
echo "Cleaning previous builds..."
rm -rf dist/ build/ *.egg-info 2>/dev/null || true

# Build the package
echo "Building distribution packages..."
python -m build

# Check the build
echo
echo "Build complete. Contents:"
ls -la dist/

# Test the package (optional)
echo
read -p "Do you want to test the package locally before uploading? (y/n) " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    echo "Creating test virtual environment..."
    python -m venv test_env
    source test_env/bin/activate
    pip install dist/hanzo-0.2.5-py3-none-any.whl
    echo "Testing hanzo command..."
    hanzo --version
    deactivate
    rm -rf test_env
    echo "Test successful!"
fi

# Upload to TestPyPI first (optional)
echo
read -p "Do you want to upload to TestPyPI first? (y/n) " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    echo "Uploading to TestPyPI..."
    python -m twine upload --repository testpypi dist/*
    echo
    echo "Package uploaded to TestPyPI."
    echo "Test with: pip install --index-url https://test.pypi.org/simple/ hanzo"
    echo
    read -p "Continue to PyPI? (y/n) " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        echo "Stopping here. Package is on TestPyPI."
        exit 0
    fi
fi

# Upload to PyPI
echo
echo "Uploading to PyPI..."
echo "You will be prompted for your PyPI credentials or API token."
echo
python -m twine upload dist/*

echo
echo "=================================="
echo "Package published successfully!"
echo "Install with: pip install hanzo"
echo "Current version: 0.2.5"
echo "=================================="