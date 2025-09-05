# Streamlined AI Coding Workflow with Hanzo-MCP

## Core Configuration

### 1. Disable Hanzo FS Editors in Settings
```json
// Claude Desktop settings.json
{
  "mcpServers": {
    "hanzo-mcp": {
      "command": "hanzo-mcp",
      "args": ["serve"],
      "env": {
        "HANZO_MCP_DISABLED_TOOLS": "write,edit,multi_edit,neovim_edit,neovim_command"
      }
    }
  }
}
```

### 2. Use OpenAI Tools for File I/O
- `Read` - Read files from filesystem
- `Write` - Write new files  
- `Edit` - Edit existing files
- `MultiEdit` - Multiple edits in one operation

### 3. Hanzo-MCP Tool Usage

#### Planning Phase - Architecture Generation
```bash
# Single model architecture
llm --action query \
  --model claude-3-opus-20240229 \
  --prompt "Design architecture for [feature]" \
  --system-prompt "You are a senior architect. Output markdown format."

# Consensus architecture (multiple models)
llm --action consensus \
  --models '["claude-3-opus-20240229", "gpt-4-turbo", "gemini-1.5-pro"]' \
  --prompt "Design architecture for user authentication system" \
  --system-prompt "Create architectural consensus following zen principles"
```

Save output to `architecture.md` using OpenAI Write tool.

#### Task Tracking - Todo Tool
```bash
# Add tasks from architecture
todo --action add --content "Implement JWT service" --priority high
todo --action add --content "Create auth middleware" --priority high  
todo --action add --content "Add user session management" --priority medium

# Track progress
todo --action list --filter pending
todo --action update --id task1 --status in_progress
todo --action update --id task1 --status completed
```

**Note**: Todo storage is in-memory per MCP session (not persisted to files).

#### Execution - Agent per Todo
```bash
# For each todo item, dispatch an agent
agent --prompt """
Task: [todo content from list]
1. Create git worktree: git worktree add -b feature/[name] ../[name]
2. Implement the feature following architecture.md
3. Write tests
4. Commit with descriptive message
Return: Summary of implementation and any issues
"""

# Agent automatically has access to:
# - read (for reading files)
# - run_command (for git operations)
# - search (for finding patterns)
# - grep_ast (for code structure analysis)
```

#### QA - Critic Tool
```bash
# After agent completes implementation
critic --analysis """
Review the implementation in worktree [name]:
- Check for bugs and edge cases
- Verify it follows architecture.md patterns
- Ensure proper error handling
- Validate test coverage
- Security implications
Return: List of issues to fix or 'APPROVED'
"""
```

## Complete Workflow Example

```python
# PHASE 1: PLANNING
# Generate architecture with consensus
architecture = llm(
    action="consensus",
    models=["claude-3-opus-20240229", "gpt-4-turbo"],
    prompt="Design OAuth2 integration architecture"
)

# Save to architecture.md (using OpenAI Write)
Write("architecture.md", architecture)

# PHASE 2: TASK GENERATION  
# Break into tasks
tasks = llm(
    action="query",
    model="claude-3-opus-20240229",
    prompt=f"Break down this architecture into small tasks:\n{architecture}"
)

# Add to todo list
for task in tasks:
    todo(action="add", content=task.description, priority=task.priority)

# PHASE 3: EXECUTION
# Get pending todos
pending = todo(action="list", filter="pending")

for task in pending:
    # Update status
    todo(action="update", id=task.id, status="in_progress")
    
    # Create worktree and implement
    result = agent(prompt=f"""
        Create worktree: feature/{task.id}
        Implement: {task.content}
        Follow: architecture.md
        Test and commit
    """)
    
    # QA Review
    review = critic(analysis=f"""
        Review implementation in feature/{task.id}
        Check against architecture.md
    """)
    
    if "APPROVED" in review:
        todo(action="update", id=task.id, status="completed")
    else:
        # Fix issues
        agent(prompt=f"Fix these issues in feature/{task.id}: {review}")

# PHASE 4: INTEGRATION
# Merge all completed worktrees
completed = todo(action="list", filter="completed")
for task in completed:
    run_command(f"git merge feature/{task.id}")
```

## Linear Integration (Optional)

### Install Linear MCP Server
```bash
npm install -g @modelcontextprotocol/server-linear
```

### Configure in Claude Desktop
```json
{
  "mcpServers": {
    "linear": {
      "command": "node",
      "args": ["@modelcontextprotocol/server-linear/index.js"],
      "env": {
        "LINEAR_API_KEY": "lin_api_..."
      }
    }
  }
}
```

### Use Agent to Create Linear Issues
```bash
agent --prompt """
Using Linear MCP tools:
1. Create project 'OAuth Integration'
2. For each todo item, create a Linear issue:
   - Title: [todo content]
   - Description: Reference architecture.md section
   - Priority: Map from todo priority
   - Add dependencies between issues
3. Link git worktree branches to Linear issues
Return: Linear project and issue IDs
"""
```

## Key Advantages of This Approach

1. **Clean Separation**: OpenAI handles files, Hanzo handles orchestration
2. **In-Memory Todos**: Fast, session-based task tracking without file clutter  
3. **Parallel Execution**: Agents can work on multiple worktrees simultaneously
4. **Quality Gates**: Critic ensures each piece meets standards before integration
5. **Optional Persistence**: Linear provides persistent task tracking when needed

## Quick Start Commands

```bash
# 1. Start hanzo-mcp with disabled FS tools
export HANZO_MCP_DISABLED_TOOLS="write,edit,multi_edit,neovim_edit"
hanzo-mcp serve

# 2. Generate architecture
llm --action consensus --models '["claude-3-opus", "gpt-4"]' --prompt "Design [feature]"

# 3. Create tasks
todo --action add --content "Task 1" --priority high
todo --action add --content "Task 2" --priority medium

# 4. Execute with agents
agent --prompt "Implement Task 1 in worktree feature/task1"

# 5. Review with critic
critic --analysis "Review feature/task1 implementation"

# 6. Check progress
todo --action list
```

## Session Management

Since todos are in-memory per MCP session:
- Todos persist during the session
- Cleared when MCP server restarts
- Use Linear for persistence across sessions
- Or export todos before ending session:
  ```bash
  todo --action list > session_todos.json
  ```

This streamlined approach maximizes efficiency by using each tool for its strength: OpenAI for file operations, hanzo-mcp for orchestration and planning, and optional Linear for persistent project management.