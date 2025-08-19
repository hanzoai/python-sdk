# 🚀 Quick Start: Run GPT-5 Pro + Codex Orchestration

## Step 1: Check Installation

```bash
# Check if hanzo is installed
hanzo --version

# If not installed, install it:
pip install hanzo

# Or install from this directory:
pip install -e pkg/hanzo/
```

## Step 2: Set API Keys

```bash
# Set your OpenAI API key (required for GPT-5/Codex)
export OPENAI_API_KEY="sk-..."

# Optional: Set Anthropic key for Claude models
export ANTHROPIC_API_KEY="sk-ant-..."

# Optional: Set hanzo router endpoint if using router mode
export HANZO_ROUTER_URL="http://localhost:4000"
```

## Step 3: Run Different Configurations

### Option A: GPT-5 Pro + Codex (Best for Code)
```bash
hanzo dev --orchestrator gpt-5-pro-codex
```

### Option B: Via Hanzo Router
```bash
# First, start the router (in another terminal)
hanzo router start

# Then run dev with router
hanzo dev --orchestrator router:gpt-5
```

### Option C: Direct Codex Mode
```bash
hanzo dev --orchestrator codex
```

### Option D: Cost-Optimized (90% Savings)
```bash
# Start local AI first
hanzo net --models llama-3.2-3b --port 52415

# Then run with hybrid mode
hanzo dev --orchestrator cost-optimized --use-hanzo-net
```

## Step 4: Interactive Commands

Once running, you can interact with the orchestrator:

```bash
# In the hanzo dev REPL:
> review my code for security issues
> generate a REST API for user management
> refactor this function for better performance
> add comprehensive tests to this module
> explain this architecture decision
```

## Complete Example Session

```bash
# Terminal 1: Start local AI (optional, for cost savings)
$ hanzo net --models llama-3.2-3b
Starting Hanzo Net Compute Node
✓ Model loaded: llama-3.2-3b
Serving at http://localhost:52415

# Terminal 2: Start hanzo router (optional, for router mode)
$ hanzo router start
Hanzo Router v1.74.3
Serving at http://localhost:4000
Connected providers: OpenAI, Anthropic, Google, Mistral

# Terminal 3: Run the orchestrator
$ hanzo dev --orchestrator gpt-5-pro-codex --instances 3
Orchestrator Configuration
  Mode: hybrid
  Primary Model: gpt-5-pro
  Codex Model: code-davinci-002
  Cost Optimization: Enabled

Hanzo Dev - AI Coding OS
✓ GPT-5 Pro orchestrator initialized
✓ Codex connected for code generation
✓ 3 worker agents ready
✓ MCP tools enabled
✓ Cost-optimized routing active

Ready for commands...
> 
```

## Available Commands in REPL

```bash
> help                    # Show available commands
> status                  # Show agent status
> review <file>          # Review code file
> generate <description> # Generate code
> refactor <code>        # Refactor existing code
> test <module>          # Generate tests
> debug <error>          # Debug an issue
> explain <concept>      # Explain code/architecture
> optimize <code>        # Optimize performance
> secure <code>          # Security audit
> document <code>        # Generate documentation
```

## Monitor Performance

```bash
# In another terminal, monitor the orchestrator
$ hanzo dev --monitor
┌─────────────────────────────────┐
│ Orchestrator Status             │
├─────────────────────────────────┤
│ Model: GPT-5 Pro                │
│ Workers: 3/3 active             │
│ Tasks: 12 completed, 2 pending  │
│ Cost: $0.45 (this session)      │
│ Tokens: 45,231 / 128,000        │
└─────────────────────────────────┘
```

## Troubleshooting

```bash
# If you get API key errors:
echo $OPENAI_API_KEY  # Check if set
export OPENAI_API_KEY="sk-..."  # Set it

# If hanzo command not found:
pip install hanzo  # Install globally
# OR
python -m hanzo.cli dev --orchestrator gpt-5-pro-codex  # Run as module

# If port already in use:
hanzo dev --orchestrator gpt-5-pro-codex --hanzo-net-port 52416

# Check logs:
tail -f ~/.hanzo/dev/logs/orchestrator.log
```

## Cost Tracking

```bash
# Check your usage
$ hanzo metrics
Today's Usage:
  GPT-5 Pro: $2.45 (16,300 tokens)
  Codex: $0.80 (40,000 tokens)
  GPT-4o: $1.20 (24,000 tokens)
  Local Models: $0.00 (120,000 tokens)
  Total: $4.45
  Savings: $12.55 (74% saved via optimization)
```

## Pro Tips

1. **Start with cost-optimized mode** to save money while testing
2. **Use router mode** for automatic failover between providers
3. **Enable monitoring** to track performance and costs
4. **Use local models** for simple tasks (formatting, linting)
5. **Reserve GPT-5 Pro** for complex architectural decisions

## Full Production Setup

```bash
#!/bin/bash
# save as: start-hanzo-dev.sh

# Start local AI
echo "Starting local AI..."
hanzo net --models llama-3.2-3b --port 52415 &
LOCAL_PID=$!

# Wait for local AI to be ready
sleep 5

# Start router (optional)
echo "Starting hanzo router..."
hanzo router start --port 4000 &
ROUTER_PID=$!

# Wait for router
sleep 3

# Start orchestrator with GPT-5 Pro + Codex
echo "Starting GPT-5 Pro + Codex orchestrator..."
hanzo dev \
  --orchestrator gpt-5-pro-codex \
  --instances 3 \
  --critic-instances 2 \
  --enable-guardrails \
  --use-hanzo-net \
  --workspace . \
  --monitor

# Cleanup on exit
trap "kill $LOCAL_PID $ROUTER_PID" EXIT
```

Make it executable and run:
```bash
chmod +x start-hanzo-dev.sh
./start-hanzo-dev.sh
```