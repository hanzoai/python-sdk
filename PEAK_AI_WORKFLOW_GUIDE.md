# Peak AI Coding Workflow with Hanzo-MCP

This guide shows how to use hanzo-mcp tools to orchestrate the complete AI coding workflow with multiple LLMs working in concert.

## Available Tools in Hanzo-MCP

### Core Orchestration Tools

1. **`llm` tool** - Query any LLM provider directly
   - Actions: `query`, `consensus`, `list`, `models`, `test`
   - Supports 100+ LLM providers via LiteLLM
   - Can run consensus mode with multiple models

2. **`agent` tool** - Dispatch autonomous sub-agents
   - Can recursively call other MCP tools
   - Supports concurrent task execution
   - Has access to filesystem, search, and analysis tools

3. **`swarm` tool** - Orchestrate multiple agents
   - Hierarchical or peer network architectures
   - Inter-agent communication
   - Task distribution and result aggregation

4. **`todo` tool** - Task management
   - Actions: `list`, `add`, `update`, `remove`, `clear`
   - Status tracking: pending, in_progress, completed
   - Priority levels: high, medium, low

5. **CLI Agent Tools** - Direct access to specific AI assistants
   - `claude` - Claude via CLI
   - `codex` - OpenAI Codex/GPT-4
   - `gemini` - Google Gemini
   - `grok` - xAI Grok

## Workflow Implementation

### Phase 1: Architecture & Planning

```yaml
# Step 1: Have multiple AIs independently scan and propose architecture
- Use `llm` tool with consensus mode:
  action: consensus
  models: ["claude-3-opus-20240229", "gpt-4-turbo", "gemini-1.5-pro"]
  prompt: |
    Analyze the project structure and propose an architecture for [FEATURE].
    Consider:
    - Existing patterns and conventions
    - Scalability and maintainability
    - Performance implications
    - Testing strategy
  system_prompt: |
    You are a senior architect. Follow zen principles and create 
    consensus with other models.

# Step 2: Improve with GPT-5 Pro (external)
- Copy consensus result to GPT-5 Pro web/app
- Get improved architecture proposal

# Step 3: Save as LLM.md
- Use `write` tool to save final architecture to LLM.md
```

### Phase 2: Task Generation

```yaml
# Step 1: Generate Linear-style tasks
- Use `llm` tool:
  action: query
  model: "claude-3-opus-20240229"
  prompt: |
    Based on the architecture in LLM.md, create small Linear tasks 
    that a junior engineer could complete in under a day.
    Format as JSON array with: title, description, dependencies, priority

# Step 2: Refine with GPT-5 Pro
- Send task list to GPT-5 Pro for refinement

# Step 3: Create in task system
- Use `todo` tool:
  action: add
  For each task:
    content: [task description]
    priority: [high/medium/low]
    status: pending
```

### Phase 3: Implementation

```yaml
# For each task:

# Step 1: Create worktree branch
- Use `run_command`:
  command: git worktree add -b feature/[task-name] ../[task-name]

# Step 2: First implementation with Codex
- Use `codex` tool:
  prompt: |
    Complete the task: [task description]
    Follow the architecture in LLM.md
    Reference: Linear issue #[number]

# Step 3: Code review with Claude
- Use `claude` tool:
  prompt: |
    Review this code for:
    - Correctness and completeness
    - Security vulnerabilities
    - Performance issues
    - Best practices

# Step 4: Apply feedback
- Use `codex` tool with feedback:
  prompt: |
    Apply these improvements from code review:
    [feedback points]

# Step 5: Push and create PR
- Use `run_command`:
  command: |
    git add -A
    git commit -m "[task]: Implementation"
    git push -u origin feature/[task-name]
    gh pr create --title "[task]" --body "[description]"
```

### Phase 4: Review & Merge

```yaml
# Step 1: Multi-agent PR review
- Use `swarm` tool:
  mode: peer
  agents:
    - name: security_reviewer
      model: "claude-3-opus-20240229"
      prompt: "Review PR for security issues"
    - name: performance_reviewer  
      model: "gpt-4-turbo"
      prompt: "Review PR for performance"
    - name: design_reviewer
      model: "gemini-1.5-pro"
      prompt: "Review PR for design patterns"

# Step 2: Address feedback
- Collect all feedback
- Use `codex` tool to implement changes

# Step 3: Final merge
- When no more feedback:
  command: gh pr merge --squash
```

## Example Commands for Claude

### Using LLM Tool

```bash
# Single query
llm --action query --model gpt-4-turbo --prompt "Explain this code pattern"

# Consensus mode with multiple models
llm --action consensus \
  --models '["claude-3-opus-20240229", "gpt-4-turbo", "gemini-1.5-pro"]' \
  --prompt "Propose architecture for user authentication system"

# List available models
llm --action models
```

### Using Agent Tool

```bash
# Dispatch agent for research
agent --prompt "Research all authentication patterns in /src and summarize"

# Dispatch agent for implementation
agent --prompt "Implement the UserService class based on the pattern in /src/services"
```

### Using Swarm Tool

```bash
# Orchestrate multiple agents for comprehensive analysis
swarm --mode hierarchical \
  --coordinator_prompt "Coordinate analysis of the codebase" \
  --worker_prompts '[
    "Analyze security aspects",
    "Review performance patterns",
    "Document API endpoints"
  ]'
```

### Using Todo Tool

```bash
# Add task
todo --action add --content "Implement user authentication" --priority high

# Update status
todo --action update --id abc123 --status in_progress

# List all tasks
todo --action list --filter pending
```

### Using CLI Agent Tools

```bash
# Use Claude for analysis
claude "Analyze the architecture and suggest improvements"

# Use Codex for implementation
codex "Implement the feature described in task #123"

# Use Gemini for review
gemini "Review this code for best practices"

# Use Grok for optimization
grok "Suggest performance optimizations for this algorithm"
```

## Environment Setup

### Required Environment Variables

```bash
# For LLM tool (at least one provider)
export OPENAI_API_KEY=sk-...
export ANTHROPIC_API_KEY=sk-ant-...
export GEMINI_API_KEY=...
export XAI_API_KEY=...  # For Grok

# For GitHub integration
export GITHUB_TOKEN=ghp_...

# For hanzo-mcp server
export HANZO_MCP_ALLOWED_PATHS=/path/to/project
```

### Starting the MCP Server

```bash
# Install hanzo-mcp
pip install hanzo-mcp

# Start server with all tools enabled
hanzo-mcp serve \
  --enable-agent-tool \
  --agent-model "claude-3-opus-20240229" \
  --agent-max-iterations 10

# Or configure Claude Desktop
hanzo-mcp install-desktop
```

## Advanced Patterns

### 1. Parallel Architecture Analysis

```python
# Use swarm for parallel analysis
results = swarm(
    mode="peer",
    agents=[
        {"model": "claude-3-opus", "task": "Analyze data flow"},
        {"model": "gpt-4", "task": "Review API design"},
        {"model": "gemini-1.5", "task": "Evaluate scalability"}
    ]
)
```

### 2. Recursive Task Decomposition

```python
# Agent can spawn sub-agents
agent(
    prompt="""
    Break down the authentication feature into subtasks.
    For each subtask, spawn a sub-agent to implement it.
    Coordinate the results into a cohesive solution.
    """
)
```

### 3. Consensus-Driven Design

```python
# Get consensus on critical decisions
consensus_result = llm(
    action="consensus",
    models=["claude-3-opus", "gpt-4", "gemini-1.5"],
    prompt="Should we use JWT or session-based auth?",
    voting_method="weighted"  # Based on model confidence
)
```

### 4. Automated Review Pipeline

```python
# Chain multiple review stages
pipeline = [
    ("codex", "Initial implementation"),
    ("claude", "Security review"),
    ("gpt-4", "Performance optimization"),
    ("gemini", "Documentation"),
    ("consensus", "Final approval")
]

for tool, task in pipeline:
    result = execute_tool(tool, task)
    if not result.approved:
        restart_pipeline()
```

## Tips for Effective Orchestration

1. **Use Consensus for Critical Decisions**
   - Architecture choices
   - Security implementations
   - API design decisions

2. **Leverage Parallel Execution**
   - Use `swarm` for independent tasks
   - Run multiple `agent` tools concurrently
   - Batch todo operations

3. **Maintain Context with LLM.md**
   - Update after each major decision
   - Include learned patterns
   - Document architectural constraints

4. **Task Granularity**
   - Keep tasks under 4 hours of work
   - Clear acceptance criteria
   - Explicit dependencies

5. **Review Stages**
   - Security (Claude)
   - Performance (GPT-4)
   - Best Practices (Gemini)
   - Integration (Consensus)

## Troubleshooting

### LLM Tool Not Finding API Keys
```bash
# Check available providers
llm --action list

# Test specific provider
llm --action test --model gpt-4
```

### Agent Tool Timeout
```bash
# Increase timeout and iterations
agent --max-iterations 20 --max-tokens 4000
```

### Swarm Coordination Issues
```bash
# Use hierarchical mode for better coordination
swarm --mode hierarchical --coordinator-model claude-3-opus
```

## Integration with Linear

While hanzo-mcp doesn't have direct Linear integration yet, you can:

1. Export tasks as JSON from todo tool
2. Use Linear's API via `run_command` with curl
3. Create a custom MCP tool for Linear integration

## Next Steps

1. Set up environment variables for all LLM providers
2. Configure Claude Desktop with hanzo-mcp
3. Create project-specific prompts and templates
4. Establish review criteria for each stage
5. Document patterns in LLM.md as you discover them

This workflow enables true AI orchestration where multiple models collaborate, review each other's work, and iteratively improve the codebase while maintaining high quality standards.