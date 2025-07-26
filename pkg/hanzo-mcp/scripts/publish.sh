#!/usr/bin/env bash
set -e

# ANSI color codes
GREEN='\033[0;32m'
YELLOW='\033[0;33m'
RED='\033[0;31m'
BLUE='\033[0;34m'
RESET='\033[0m'

# Get current version
CURRENT_VERSION=$(grep -E '^version = ' pyproject.toml | sed 's/version = "//g' | sed 's/"//g')

echo -e "${BLUE}Hanzo MCP Publishing Script${RESET}"
echo -e "${GREEN}Current version: ${CURRENT_VERSION}${RESET}"
echo ""

# Check if we're in the right directory
if [ ! -f "pyproject.toml" ] || [ ! -d "hanzo_mcp" ]; then
    echo -e "${RED}Error: Must run from pkg/mcp directory${RESET}"
    exit 1
fi

# Check for uncommitted changes
if ! git diff-index --quiet HEAD --; then
    echo -e "${YELLOW}Warning: You have uncommitted changes${RESET}"
    read -p "Continue anyway? (y/N) " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        exit 1
    fi
fi

# Run tests
echo -e "${GREEN}Running tests...${RESET}"
if command -v pytest &> /dev/null; then
    pytest -v || {
        echo -e "${RED}Tests failed! Fix issues before publishing.${RESET}"
        exit 1
    }
else
    echo -e "${YELLOW}pytest not found, skipping tests${RESET}"
fi

# Run linting
echo -e "${GREEN}Running linting...${RESET}"
if command -v ruff &> /dev/null; then
    ruff check hanzo_mcp/ || {
        echo -e "${RED}Linting failed! Fix issues before publishing.${RESET}"
        exit 1
    }
else
    echo -e "${YELLOW}ruff not found, skipping linting${RESET}"
fi

# Clean build artifacts
echo -e "${GREEN}Cleaning build artifacts...${RESET}"
rm -rf build/ dist/ *.egg-info

# Build packages
echo -e "${GREEN}Building distribution packages...${RESET}"
python -m build || {
    echo -e "${RED}Build failed!${RESET}"
    echo -e "${YELLOW}Make sure you have 'build' installed: pip install build${RESET}"
    exit 1
}

# Show built packages
echo -e "${GREEN}Built packages:${RESET}"
ls -la dist/

# Check for PyPI credentials
if [ ! -f ~/.pypirc ]; then
    echo -e "${YELLOW}Warning: ~/.pypirc not found${RESET}"
    echo -e "You can create one with your PyPI API token:"
    echo -e "[pypi]"
    echo -e "  username = __token__"
    echo -e "  password = <your-api-token>"
    echo ""
fi

# Ask which registry to publish to
echo -e "${YELLOW}Where would you like to publish?${RESET}"
echo "1) Test PyPI (recommended for testing)"
echo "2) PyPI (production)"
echo "3) Skip publishing"
read -p "Choose (1-3): " choice

case $choice in
    1)
        echo -e "${GREEN}Publishing to Test PyPI...${RESET}"
        twine upload --repository testpypi dist/* || {
            echo -e "${RED}Upload failed!${RESET}"
            echo -e "${YELLOW}Make sure you have twine installed: pip install twine${RESET}"
            exit 1
        }
        echo -e "${GREEN}Published to Test PyPI!${RESET}"
        echo -e "Install with: pip install -i https://test.pypi.org/simple/ hanzo-mcp==${CURRENT_VERSION}"
        ;;
    2)
        echo -e "${RED}Publishing to PyPI...${RESET}"
        echo -e "${YELLOW}This will publish version ${CURRENT_VERSION} to the official PyPI${RESET}"
        read -p "Are you REALLY sure? (yes/no): " confirm
        if [ "$confirm" == "yes" ]; then
            twine upload dist/* || {
                echo -e "${RED}Upload failed!${RESET}"
                exit 1
            }
            echo -e "${GREEN}Successfully published hanzo-mcp ${CURRENT_VERSION} to PyPI!${RESET}"
            echo -e "Install with: pip install hanzo-mcp==${CURRENT_VERSION}"
            
            # Create git tag
            echo -e "${GREEN}Creating git tag...${RESET}"
            git tag -a "mcp-v${CURRENT_VERSION}" -m "Release hanzo-mcp ${CURRENT_VERSION}"
            echo -e "${YELLOW}Don't forget to push the tag: git push origin mcp-v${CURRENT_VERSION}${RESET}"
        else
            echo -e "${YELLOW}Publishing cancelled.${RESET}"
        fi
        ;;
    3)
        echo -e "${YELLOW}Skipping publishing. Packages are in dist/${RESET}"
        ;;
    *)
        echo -e "${RED}Invalid choice${RESET}"
        exit 1
        ;;
esac

echo -e "${GREEN}Done!${RESET}"