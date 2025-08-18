#!/bin/bash

# E2E Test Runner for Hanzo Net Local AI Orchestration
set -e

echo "=============================================="
echo "Hanzo Net E2E Test Runner"
echo "=============================================="

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

# Parse arguments
RUN_SETUP=false
MODEL="qwen3"
QUICK_TEST=false

while [[ $# -gt 0 ]]; do
    case $1 in
        --setup)
            RUN_SETUP=true
            shift
            ;;
        --model)
            MODEL="$2"
            shift 2
            ;;
        --quick)
            QUICK_TEST=true
            shift
            ;;
        --help)
            echo "Usage: $0 [options]"
            echo ""
            echo "Options:"
            echo "  --setup       Run model setup before testing"
            echo "  --model NAME  Specify model to test (default: qwen3)"
            echo "  --quick       Run quick test (single model only)"
            echo "  --help        Show this help message"
            exit 0
            ;;
        *)
            echo "Unknown option: $1"
            echo "Use --help for usage information"
            exit 1
            ;;
    esac
done

# Check Python version
PYTHON_VERSION=$(python3 --version | cut -d' ' -f2 | cut -d'.' -f1-2)
REQUIRED_VERSION="3.9"

if [[ $(echo "$PYTHON_VERSION < $REQUIRED_VERSION" | bc) -eq 1 ]]; then
    echo -e "${RED}Error: Python $REQUIRED_VERSION or higher required (found $PYTHON_VERSION)${NC}"
    exit 1
fi

# Run setup if requested
if [ "$RUN_SETUP" = true ]; then
    echo -e "${YELLOW}Running model setup...${NC}"
    bash setup_models.sh
    echo ""
fi

# Check if hanzo is installed
if ! command -v hanzo >/dev/null 2>&1; then
    echo -e "${RED}Error: hanzo CLI not found${NC}"
    echo "Please install it first:"
    echo "  cd ../../.."
    echo "  pip install -e pkg/hanzo/"
    exit 1
fi

# Check if hanzo-network is installed
if ! python3 -c "import hanzo_network" 2>/dev/null; then
    echo -e "${YELLOW}Installing hanzo-network...${NC}"
    pip install -e ../../../pkg/hanzo-network/
fi

# Export API keys if they exist in .env
if [ -f .env ]; then
    export $(grep -v '^#' .env | xargs)
fi

# Start hanzo net if not running
echo "Checking hanzo net status..."
if ! nc -z localhost 52415 2>/dev/null; then
    echo -e "${YELLOW}Starting hanzo net with $MODEL...${NC}"
    
    hanzo net \
        --name "e2e-test" \
        --port 52415 \
        --models "$MODEL" \
        --network local \
        --max-jobs 10 &
    
    HANZO_NET_PID=$!
    
    # Wait for hanzo net to start
    echo -n "Waiting for hanzo net to start"
    for i in {1..30}; do
        if nc -z localhost 52415 2>/dev/null; then
            echo -e " ${GREEN}✓${NC}"
            break
        fi
        echo -n "."
        sleep 1
    done
    
    if ! nc -z localhost 52415 2>/dev/null; then
        echo -e " ${RED}✗${NC}"
        echo "Failed to start hanzo net"
        exit 1
    fi
else
    echo -e "${GREEN}✓ hanzo net already running${NC}"
fi

# Run the test
echo ""
echo "Starting E2E test..."
echo "=============================================="

if [ "$QUICK_TEST" = true ]; then
    # Quick test - single model only
    python3 -c "
import asyncio
import sys
sys.path.insert(0, '../../..')
from tests.e2e.hanzo_net_orchestration.test_local_ai_orchestration import HanzoNetE2ETest

async def quick_test():
    test = HanzoNetE2ETest()
    test.models_to_test = ['$MODEL']
    await test.run_full_test()

asyncio.run(quick_test())
"
else
    # Full test
    python3 test_local_ai_orchestration.py
fi

TEST_RESULT=$?

# Cleanup
if [ ! -z "$HANZO_NET_PID" ]; then
    echo ""
    echo "Stopping hanzo net..."
    kill $HANZO_NET_PID 2>/dev/null || true
fi

# Report results
echo ""
echo "=============================================="
if [ $TEST_RESULT -eq 0 ]; then
    echo -e "${GREEN}✓ E2E Test Passed${NC}"
else
    echo -e "${RED}✗ E2E Test Failed${NC}"
fi
echo "=============================================="

exit $TEST_RESULT