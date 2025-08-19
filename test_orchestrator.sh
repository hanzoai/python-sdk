#!/bin/bash
# Test script to demonstrate different orchestrator configurations

echo "╔════════════════════════════════════════════════════════════╗"
echo "║           Hanzo Dev - Orchestrator Test Suite             ║"
echo "╚════════════════════════════════════════════════════════════╝"
echo ""

# Function to test a configuration
test_config() {
    local name="$1"
    local cmd="$2"
    local description="$3"
    
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo "📦 Testing: $name"
    echo "📝 Description: $description"
    echo "💻 Command: $cmd"
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    
    # Run the command with a timeout and capture initial output
    timeout 5s bash -c "$cmd" 2>&1 | head -20
    
    echo ""
}

# Test 1: GPT-5 Pro + Codex
test_config \
    "GPT-5 Pro + Codex" \
    "hanzo dev --orchestrator gpt-5-pro-codex --instances 2" \
    "Ultimate code development with GPT-5 Pro reasoning + Codex generation"

# Test 2: Router mode
test_config \
    "Router Mode (GPT-4o)" \
    "hanzo dev --orchestrator router:gpt-4o" \
    "Access GPT-4o via hanzo-router with automatic failover"

# Test 3: Direct Codex
test_config \
    "Direct Codex" \
    "hanzo dev --orchestrator codex" \
    "Pure Codex mode for specialized code generation"

# Test 4: Cost-optimized
test_config \
    "Cost Optimized" \
    "hanzo dev --orchestrator cost-optimized --use-hanzo-net" \
    "90% cost reduction with local models + selective API usage"

# Test 5: Local model
test_config \
    "Local Llama" \
    "hanzo dev --orchestrator local:llama3.2" \
    "Pure local model orchestration (free!)"

echo "╔════════════════════════════════════════════════════════════╗"
echo "║                    Test Complete!                         ║"
echo "╚════════════════════════════════════════════════════════════╝"
echo ""
echo "To run interactively, use any of these commands:"
echo ""
echo "  hanzo dev --orchestrator gpt-5-pro-codex    # Best for code"
echo "  hanzo dev --orchestrator router:gpt-5       # Via router"
echo "  hanzo dev --orchestrator codex              # Pure Codex"
echo "  hanzo dev --orchestrator cost-optimized     # 90% savings"
echo ""
echo "For more options: hanzo dev --help"