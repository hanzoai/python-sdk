# Makefile for Hanzo Net E2E Testing

.PHONY: help setup test quick-test clean docker-up docker-down logs

# Default target
help:
	@echo "Hanzo Net E2E Test - Available Commands"
	@echo "======================================="
	@echo ""
	@echo "Setup & Installation:"
	@echo "  make setup          - Download models and start services"
	@echo "  make install        - Install hanzo and hanzo-network"
	@echo ""
	@echo "Testing:"
	@echo "  make test           - Run full E2E test suite"
	@echo "  make quick-test     - Run quick test with single model"
	@echo "  make test-qwen      - Test with Qwen3 model"
	@echo "  make test-llama     - Test with Llama 3.2 model"
	@echo "  make test-mistral   - Test with Mistral 7B"
	@echo ""
	@echo "Docker Management:"
	@echo "  make docker-up      - Start Docker services"
	@echo "  make docker-down    - Stop Docker services"
	@echo "  make logs           - View Docker logs"
	@echo ""
	@echo "Hanzo Commands:"
	@echo "  make start-net      - Start hanzo net locally"
	@echo "  make start-dev      - Start hanzo dev with local orchestrator"
	@echo "  make demo           - Run interactive demo"
	@echo ""
	@echo "Cleanup:"
	@echo "  make clean          - Stop all services and clean up"

# Installation
install:
	@echo "Installing hanzo and dependencies..."
	@cd ../../.. && pip install -e pkg/hanzo/
	@cd ../../.. && pip install -e pkg/hanzo-network/
	@cd ../../.. && pip install -e pkg/hanzo-mcp/
	@echo "✓ Installation complete"

# Setup models and services
setup: install
	@echo "Setting up models and services..."
	@bash setup_models.sh
	@echo "✓ Setup complete"

# Run full test suite
test: install
	@echo "Running full E2E test suite..."
	@bash run_test.sh

# Quick test with default model
quick-test: install
	@echo "Running quick test..."
	@bash run_test.sh --quick

# Test specific models
test-qwen: install
	@echo "Testing with Qwen3..."
	@bash run_test.sh --model qwen3 --quick

test-llama: install
	@echo "Testing with Llama 3.2..."
	@bash run_test.sh --model llama-3.2-3b --quick

test-mistral: install
	@echo "Testing with Mistral 7B..."
	@bash run_test.sh --model mistral-7b --quick

test-deepseek: install
	@echo "Testing with DeepSeek..."
	@bash run_test.sh --model deepseek-v3 --quick

# Docker management
docker-up:
	@echo "Starting Docker services..."
	@docker-compose up -d
	@echo "✓ Services started"
	@echo "Run 'make logs' to view logs"

docker-down:
	@echo "Stopping Docker services..."
	@docker-compose down
	@echo "✓ Services stopped"

logs:
	@docker-compose logs -f

# Start hanzo net manually
start-net:
	@echo "Starting hanzo net with Qwen3..."
	hanzo net \
		--name "e2e-test" \
		--port 52415 \
		--models qwen3 \
		--network local \
		--max-jobs 10

# Start hanzo dev with local orchestrator
start-dev:
	@echo "Starting hanzo dev with local orchestrator..."
	hanzo dev \
		--orchestrator local:qwen3 \
		--use-hanzo-net \
		--instances 3

# Interactive demo
demo: install
	@echo "Starting interactive demo..."
	@echo ""
	@echo "This will:"
	@echo "1. Start hanzo net with Qwen3"
	@echo "2. Launch hanzo dev with local orchestrator"
	@echo "3. Create a network of local + API agents"
	@echo ""
	@read -p "Press Enter to continue..."
	@bash -c "hanzo net --models qwen3 --network local &"
	@sleep 5
	@hanzo dev --orchestrator local:qwen3 --use-hanzo-net

# Run specific test functions
test-routing: install
	@python3 -c "import asyncio; from test_local_ai_orchestration import HanzoNetE2ETest; \
		t = HanzoNetE2ETest(); \
		asyncio.run(t.setup()); \
		asyncio.run(t.start_hanzo_net('qwen3')); \
		network = asyncio.run(t.create_agent_network('qwen3')); \
		asyncio.run(t.test_task_routing(network))"

test-cost: install
	@python3 -c "import asyncio; from test_local_ai_orchestration import HanzoNetE2ETest; \
		t = HanzoNetE2ETest(); \
		asyncio.run(t.setup()); \
		asyncio.run(t.start_hanzo_net('qwen3')); \
		network = asyncio.run(t.create_agent_network('qwen3')); \
		asyncio.run(t.test_cost_optimization(network))"

test-integration: install
	@python3 -c "import asyncio; from test_local_ai_orchestration import HanzoNetE2ETest; \
		t = HanzoNetE2ETest(); \
		asyncio.run(t.setup()); \
		asyncio.run(t.start_hanzo_net('qwen3')); \
		asyncio.run(t.test_hanzo_dev_integration('qwen3'))"

# Cleanup
clean:
	@echo "Cleaning up..."
	@-pkill -f "hanzo net" 2>/dev/null || true
	@-pkill -f "hanzo dev" 2>/dev/null || true
	@-docker-compose down 2>/dev/null || true
	@echo "✓ Cleanup complete"

# Check system requirements
check-requirements:
	@echo "Checking system requirements..."
	@echo ""
	@echo -n "Python: "
	@python3 --version
	@echo -n "Docker: "
	@docker --version || echo "Not installed"
	@echo -n "Docker Compose: "
	@docker-compose --version || docker compose version || echo "Not installed"
	@echo ""
	@echo "Checking API keys..."
	@[ -n "$$OPENAI_API_KEY" ] && echo "✓ OPENAI_API_KEY set" || echo "✗ OPENAI_API_KEY not set"
	@[ -n "$$ANTHROPIC_API_KEY" ] && echo "✓ ANTHROPIC_API_KEY set" || echo "✗ ANTHROPIC_API_KEY not set"
	@[ -n "$$GOOGLE_API_KEY" ] && echo "✓ GOOGLE_API_KEY set" || echo "✗ GOOGLE_API_KEY not set"
	@echo ""
	@echo "Checking hanzo installation..."
	@which hanzo >/dev/null 2>&1 && echo "✓ hanzo CLI installed" || echo "✗ hanzo CLI not found"
	@python3 -c "import hanzo_network" 2>/dev/null && echo "✓ hanzo-network installed" || echo "✗ hanzo-network not found"

# Performance monitoring
monitor:
	@echo "Starting performance monitor..."
	@watch -n 1 'echo "=== System Resources ===" && \
		echo "" && \
		echo "CPU & Memory:" && \
		top -l 1 | head -10 && \
		echo "" && \
		echo "Hanzo Processes:" && \
		ps aux | grep -E "hanzo (net|dev)" | grep -v grep && \
		echo "" && \
		echo "Network Ports:" && \
		lsof -i :52415 -i :11434 -i :8080 -i :8000 2>/dev/null | head -10'

# Run all tests in sequence
test-all: install
	@echo "Running all model tests..."
	@make test-qwen
	@sleep 5
	@make test-llama
	@sleep 5
	@make test-mistral
	@echo ""
	@echo "================================"
	@echo "All tests complete!"
	@echo "================================"

.DEFAULT_GOAL := help