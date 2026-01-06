# hanzo-tools-agent

Multi-agent orchestration with CLI spawning, DAG execution, swarm distribution, and Metastable consensus.

## Installation

```bash
pip install hanzo-tools-agent
```

With optional features:

```bash
pip install hanzo-tools-agent[api]   # httpx for direct API mode
pip install hanzo-tools-agent[perf]  # uvloop for high performance
pip install hanzo-tools-agent[full]  # All features
```

## Overview

`hanzo-tools-agent` provides:

- **agent** - Multi-agent orchestration (run, dag, swarm, consensus, dispatch)
- **iching** - I Ching wisdom for engineering decisions
- **review** - Code review tool

## Quick Start

```python
# Run a single agent
agent(action="run", name="claude", prompt="Explain this code")

# List available agents
agent(action="list")

# Run consensus across multiple models
agent(action="consensus", prompt="Best approach for caching?", agents=["claude", "gemini", "codex"])

# Swarm pattern - distribute work
agent(action="swarm", items=["file1.py", "file2.py"], template="Review {item}")

# DAG execution with dependencies
agent(action="dag", tasks=[
    {"id": "analyze", "prompt": "Analyze the codebase"},
    {"id": "plan", "prompt": "Create implementation plan", "after": ["analyze"]}
])
```

## Available Agents

| Agent | Description | API Key Env |
|-------|-------------|-------------|
| `claude` | Anthropic Claude Code CLI | `ANTHROPIC_API_KEY` |
| `codex` | OpenAI Codex CLI | `OPENAI_API_KEY` |
| `gemini` | Google Gemini CLI | `GOOGLE_API_KEY` |
| `grok` | xAI Grok CLI | `XAI_API_KEY` |
| `qwen` | Alibaba Qwen CLI | `DASHSCOPE_API_KEY` |
| `vibe` | Vibe coding agent | - |
| `dev` | Hanzo Dev agent | - |

## Actions Reference

### run

Run a single agent with a prompt.

```python
# Default agent (claude in Claude Code environment)
agent(action="run", prompt="Explain this error")

# Specific agent
agent(action="run", name="gemini", prompt="Review this code")

# With working directory
agent(action="run", name="codex", prompt="Fix the tests", cwd="/project/path")

# With timeout
agent(action="run", name="claude", prompt="Complex task", timeout=300)
```

**Parameters:**
- `name`: Agent to use (default: auto-detect)
- `prompt` (required): Task for the agent
- `cwd`: Working directory
- `timeout`: Timeout in seconds (default: 300)

### dag

Execute tasks with dependencies using a DAG (Directed Acyclic Graph).

```python
agent(
    action="dag",
    tasks=[
        {"id": "research", "prompt": "Research best practices for caching"},
        {"id": "design", "prompt": "Design cache architecture", "after": ["research"]},
        {"id": "implement", "prompt": "Implement the cache", "after": ["design"]},
        {"id": "test", "prompt": "Write tests", "after": ["implement"]}
    ]
)
```

**Task format:**
- `id` (required): Unique task identifier
- `prompt` (required): Task description
- `after`: List of task IDs that must complete first
- `agent`: Specific agent for this task (optional)

### swarm

Distribute work across multiple agents in parallel.

```python
# Process multiple files
agent(
    action="swarm",
    items=["auth.py", "api.py", "models.py"],
    template="Review {item} for security issues",
    max_concurrent=5
)

# Multiple prompts
agent(
    action="swarm",
    items=["Add error handling", "Add logging", "Add tests"],
    template="{item} to the authentication module"
)
```

**Parameters:**
- `items` (required): List of items to process
- `template` (required): Prompt template with `{item}` placeholder
- `max_concurrent`: Maximum parallel agents (default: 100)

### consensus

Run Metastable consensus across multiple models.

```python
agent(
    action="consensus",
    prompt="What's the best database for this use case?",
    agents=["claude", "gemini", "codex"],
    rounds=3,        # Consensus rounds
    k=3,             # Sample size per round
    alpha=0.6,       # Agreement threshold
    beta_1=0.5,      # Preference threshold
    beta_2=0.8       # Decision threshold
)
```

**Parameters:**
- `prompt` (required): Question for consensus
- `agents`: Models to participate (default: all available)
- `rounds`: Number of consensus rounds (default: 3)
- `k`: Sample size per round (default: 3)
- `alpha`: Agreement threshold (default: 0.6)
- `beta_1`: Phase I preference threshold (default: 0.5)
- `beta_2`: Phase II decision threshold (default: 0.8)

**Consensus Protocol:**
Based on [Metastable Consensus](https://github.com/luxfi/consensus):
- Phase I (Sampling): k-peer sampling, confidence accumulation
- Phase II (Finality): Threshold aggregation, winner synthesis

### dispatch

Route different tasks to different agents.

```python
agent(
    action="dispatch",
    tasks=[
        {"agent": "claude", "prompt": "Review code quality"},
        {"agent": "codex", "prompt": "Suggest optimizations"},
        {"agent": "gemini", "prompt": "Check documentation"}
    ]
)
```

### list

List all available agents.

```python
agent(action="list")
```

**Response:**
```json
{
  "agents": ["claude", "codex", "gemini", "grok", "qwen", "vibe", "dev"],
  "available": ["claude", "gemini"],
  "configured": ["claude", "codex", "gemini"]
}
```

### status

Check if a specific agent is available.

```python
agent(action="status", name="claude")
```

### config

Show agent configuration.

```python
agent(action="config")
```

## Agent Configuration

### Config Files

Configure agents via `~/.hanzo/agents/<name>.json`:

```json
{
  "cmd": "claude",
  "args": ["--print", "--dangerously-skip-permissions"],
  "env_key": "ANTHROPIC_API_KEY",
  "max_turns": 999,
  "session": true,
  "model": "claude-3-opus",
  "system_prompt": "You are a helpful assistant"
}
```

### Environment Overrides

Override arguments via environment:

```bash
export HANZO_AGENT_CLAUDE_ARGS="--verbose --model claude-3-5-sonnet"
```

### API Mode

Configure direct API calls (no CLI needed):

```json
{
  "endpoint": "https://api.openai.com/v1/chat/completions",
  "api_type": "openai",
  "model": "gpt-4",
  "env_key": "OPENAI_API_KEY",
  "system_prompt": "You are a helpful assistant"
}
```

## YOLO Mode

All agents are configured with autonomous operation flags:

| Agent | YOLO Flags |
|-------|------------|
| claude | `--dangerously-skip-permissions`, `--print`, `--output-format text` |
| codex | `--full-auto` |
| gemini | `-y`, `-q` |
| grok | `-y` |
| qwen | `--approval-mode yolo`, `-p` |
| vibe | `--auto-approve`, `--max-turns 999`, `-p` |

## Auto-Backgrounding

Long-running agents automatically background after timeout:

```python
# Long task - will auto-background
agent(action="run", name="claude", prompt="Complex refactoring task", timeout=300)

# Check status with ps tool
ps()                    # List all processes
ps(logs="agent_xxx")    # View output
ps(kill="agent_xxx")    # Stop process
```

## IChingTool

Apply I Ching wisdom to engineering challenges.

```python
iching(challenge="How should I approach refactoring this legacy codebase?")
```

**Response:**
- Hexagram interpretation
- Relevant Hanzo principles
- Actionable recommendations

## ReviewTool

Request balanced code review.

```python
review(
    focus="FUNCTIONALITY",
    work_description="Implemented auto-import feature for Go files",
    code_snippets=["func AddImport(file string) error { ... }"],
    file_paths=["/path/to/import_handler.go"],
    context="This will be used to automatically fix missing imports"
)
```

**Focus areas:**
- `GENERAL` - Overall code quality
- `FUNCTIONALITY` - Does it work correctly?
- `READABILITY` - Is it easy to understand?
- `MAINTAINABILITY` - Is it easy to modify?
- `TESTING` - Is it well tested?
- `DOCUMENTATION` - Is it well documented?
- `ARCHITECTURE` - Is the design sound?

## Examples

### Multi-Agent Code Review

```python
# Get perspectives from multiple agents
agent(
    action="consensus",
    prompt="Review this pull request for issues",
    agents=["claude", "gemini", "codex"]
)
```

### Parallel File Processing

```python
# Review all files in parallel
agent(
    action="swarm",
    items=["src/auth.py", "src/api.py", "src/models.py", "src/utils.py"],
    template="Review {item} and suggest improvements",
    max_concurrent=4
)
```

### Sequential Workflow

```python
# Plan → Implement → Test
agent(
    action="dag",
    tasks=[
        {"id": "plan", "prompt": "Create implementation plan for user auth"},
        {"id": "implement", "prompt": "Implement the plan", "after": ["plan"]},
        {"id": "test", "prompt": "Write comprehensive tests", "after": ["implement"]},
        {"id": "review", "prompt": "Review implementation", "after": ["test"]}
    ]
)
```

## Best Practices

1. **Use consensus for decisions** - Multiple perspectives reduce bias
2. **Use swarm for bulk operations** - Parallel processing is faster
3. **Use DAG for workflows** - Dependencies ensure correct ordering
4. **Configure timeouts appropriately** - Complex tasks need more time
5. **Check agent availability** - Use `status` before assuming an agent exists
