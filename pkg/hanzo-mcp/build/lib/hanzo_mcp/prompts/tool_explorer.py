"""Tool explorer prompts for discovering and using Hanzo MCP tools."""

TOOL_EXPLORER_PROMPT = """# Hanzo MCP Tool Explorer

You have access to a comprehensive suite of tools through the Hanzo MCP system. These tools can be used individually or combined using the batch tool for powerful multi-agent workflows.

## Tool Categories

### 🤖 Agent Tools
Tools for delegating tasks to specialized AI agents:
- **dispatch_agent**: Launch a specialized agent for file exploration and analysis
- **swarm**: Orchestrate multiple agents working together
- **claude_cli**: Interact with Claude via CLI
- **critic**: Critical analysis and review
- **review**: Code review and feedback
- **iching**: Decision-making guidance using I Ching

### 📁 Filesystem Tools
Tools for file and directory operations:
- **read_files**: Read one or multiple files
- **write_file**: Create or overwrite files
- **edit_file**: Make precise edits to files
- **multi_edit**: Multiple edits in one operation
- **directory_tree**: View directory structure
- **find**: Find files by pattern
- **grep**: Search file contents
- **grep_ast**: Search with AST context
- **search_content**: Unified search across multiple methods
- **symbols**: Find code symbols
- **content_replace**: Replace patterns across files
- **batch_search**: Run multiple searches in parallel

### 🐚 Shell Tools
Tools for command execution:
- **run_command**: Execute shell commands
- **bash**: Run bash commands with session persistence
- **npx**: Run Node packages
- **uvx**: Run Python packages
- **process**: Manage background processes
- **open**: Open files/URLs in default app

### 🧠 AI/LLM Tools
Tools for AI operations:
- **llm**: Query various LLM providers
- **consensus**: Get consensus from multiple models
- **think**: Structured thinking and planning
- **critic**: Critical analysis

### 💾 Database Tools
Tools for data operations:
- **sql_query**: Execute SQL queries
- **graph_add**: Add to graph database
- **vector_search**: Semantic search
- **index**: Manage search indices

### 📓 Jupyter Tools
Tools for notebook operations:
- **notebook_read**: Read Jupyter notebooks
- **notebook_edit**: Edit notebook cells

### ✅ Todo Tools
Tools for task management:
- **todo**: Manage todo lists
- **todo_read**: Read current todos
- **todo_write**: Update todo items

### 🔧 Configuration Tools
Tools for settings and configuration:
- **config**: Manage tool configuration
- **mode**: Switch developer modes
- **tool_list**: List available tools
- **tool_enable/disable**: Toggle tools

### 🔍 LSP Tools
Language Server Protocol tools:
- **lsp**: Code intelligence operations

### 🌐 MCP Tools
Model Context Protocol management:
- **mcp_add**: Add MCP servers
- **mcp_remove**: Remove MCP servers
- **mcp_stats**: View MCP statistics

## Using Tools with Batch

The batch tool allows you to run multiple tools in parallel for maximum efficiency:

```python
batch(
    description="Analyze project structure",
    invocations=[
        {"tool_name": "directory_tree", "input": {"path": "/project"}},
        {"tool_name": "grep", "input": {"pattern": "TODO", "path": "/project"}},
        {"tool_name": "find", "input": {"pattern": "*.test.js", "path": "/project"}}
    ]
)
```

## Tool Usage Examples

### Example 1: Code Analysis Workflow
```python
# First, explore the project structure
directory_tree(path="/project", depth=3)

# Search for specific patterns
batch(
    description="Find all API endpoints",
    invocations=[
        {"tool_name": "grep", "input": {"pattern": "app\\.(get|post|put|delete)", "path": "/project/src"}},
        {"tool_name": "grep_ast", "input": {"pattern": "router", "path": "/project/src"}}
    ]
)
```

### Example 2: Multi-Agent Analysis
```python
# Dispatch specialized agents for different tasks
batch(
    description="Comprehensive code analysis",
    invocations=[
        {"tool_name": "dispatch_agent", "input": {"prompt": "Analyze security vulnerabilities in /project/src"}},
        {"tool_name": "dispatch_agent", "input": {"prompt": "Find performance bottlenecks in database queries"}},
        {"tool_name": "dispatch_agent", "input": {"prompt": "Review test coverage and suggest improvements"}}
    ]
)
```

### Example 3: Refactoring Workflow
```python
# Find all instances of a pattern
search_content(pattern="oldFunction", path="/project")

# Review the code
critic(analysis="Review the usage of oldFunction and suggest refactoring approach")

# Make the changes
batch(
    description="Refactor oldFunction to newFunction",
    invocations=[
        {"tool_name": "content_replace", "input": {
            "pattern": "oldFunction",
            "replacement": "newFunction",
            "path": "/project/src"
        }},
        {"tool_name": "run_command", "input": {"command": "npm test"}}
    ]
)
```

## Best Practices

1. **Use batch for parallel operations**: When you need to run multiple independent operations, use batch to run them concurrently.

2. **Combine search tools**: Use unified_search for comprehensive results, grep for simple text matching, and grep_ast for code structure understanding.

3. **Leverage agents for complex tasks**: Use dispatch_agent for tasks requiring deep analysis or multiple steps.

4. **Track progress with todos**: Use todo tools to manage multi-step workflows.

5. **Think before acting**: Use the think tool to plan complex operations.

## Getting Started

To explore available tools in detail:
1. Use `tool_list()` to see all available tools
2. Each tool has detailed documentation in its implementation
3. Tools can be combined creatively for powerful workflows

Would you like to explore any specific tool category or see more examples?"""

# Tool category specific prompts
FILESYSTEM_TOOLS_HELP = """# Filesystem Tools Guide

## Core File Operations

### Reading Files
```python
# Read a single file
read_files(paths=["/path/to/file.py"])

# Read multiple files at once
read_files(paths=[
    "/project/src/main.py",
    "/project/src/utils.py",
    "/project/tests/test_main.py"
])

# Read with line limits
read_files(paths=["/large/file.py"], lines=100, offset=500)
```

### Editing Files
```python
# Simple edit
edit_file(
    path="/src/main.py",
    edits=[{"oldText": "old code", "newText": "new code"}]
)

# Multiple edits in one file
multi_edit(
    file_path="/src/utils.py",
    edits=[
        {"old_string": "import old", "new_string": "import new"},
        {"old_string": "old_function", "new_string": "new_function"}
    ]
)
```

### Searching
```python
# Find files by pattern
find(pattern="*.test.js", path="/project")

# Search file contents
grep(pattern="TODO|FIXME", path="/project", include="*.py")

# Search with AST context
grep_ast(pattern="class.*Controller", path="/project/src")

# Unified search (combines multiple search methods)
search_content(
    pattern="authentication",
    path="/project",
    enable_vector=True,
    enable_ast=True
)
```

### Batch Operations
```python
# Search across multiple patterns simultaneously
batch_search(
    queries=[
        {"pattern": "login", "type": "text"},
        {"pattern": "authenticate", "type": "semantic"},
        {"pattern": "class.*Auth", "type": "ast"}
    ],
    path="/project"
)
```

## Advanced Features

### Content Replacement
```python
# Replace across multiple files
content_replace(
    pattern="oldAPI",
    replacement="newAPI",
    path="/project/src",
    dry_run=True  # Preview changes first
)
```

### Directory Exploration
```python
# View directory structure
directory_tree(path="/project", depth=3, include_filtered=False)

# Find specific file types
find(
    pattern="*.py",
    path="/project",
    min_size="1KB",
    max_size="100KB",
    modified_after="1 week ago"
)
```"""

AGENT_TOOLS_HELP = """# Agent Tools Guide

## Dispatching Agents

The agent tools allow you to delegate complex tasks to specialized sub-agents that have access to file operations and search capabilities.

### Basic Agent Dispatch
```python
# Dispatch a single agent for analysis
dispatch_agent(
    prompt="Analyze the authentication system in /project/src/auth and identify security vulnerabilities"
)

# Multiple agents for different aspects
batch(
    description="Comprehensive security audit",
    invocations=[
        {"tool_name": "dispatch_agent", "input": {
            "prompt": "Review authentication implementation for security issues"
        }},
        {"tool_name": "dispatch_agent", "input": {
            "prompt": "Check for SQL injection vulnerabilities in database queries"
        }},
        {"tool_name": "dispatch_agent", "input": {
            "prompt": "Analyze API endpoints for authorization bypass risks"
        }}
    ]
)
```

### Swarm Operations
```python
# Create a swarm of agents working together
swarm(
    agents=[
        {
            "id": "analyzer",
            "role": "Code Analyzer",
            "goal": "Identify code quality issues",
            "backstory": "Expert in clean code principles",
            "tools": ["grep_ast", "read_files", "symbols"]
        },
        {
            "id": "refactorer",
            "role": "Code Refactorer",
            "goal": "Suggest and implement improvements",
            "backstory": "Specialist in code optimization",
            "tools": ["edit_file", "multi_edit", "content_replace"]
        }
    ],
    tasks=[
        {
            "description": "Find code smells and anti-patterns",
            "assigned_to": "analyzer"
        },
        {
            "description": "Refactor identified issues",
            "assigned_to": "refactorer",
            "depends_on": ["analyzer"]
        }
    ]
)
```

### Specialized Agents

#### Critic Agent
```python
# Get critical analysis
critic(
    analysis="Review this implementation for potential issues:\\n" + code_snippet
)
```

#### Review Agent
```python
# Comprehensive code review
review(
    files=["/src/main.py", "/src/utils.py"],
    focus_areas=["security", "performance", "maintainability"]
)
```

#### I Ching Guidance
```python
# Get decision-making guidance
iching(
    question="Should we refactor the authentication system now or after the release?"
)
```

## Agent Capabilities

Agents dispatched through these tools have access to:
- File reading and searching
- Pattern matching and AST analysis
- Directory exploration
- Comprehensive search capabilities

They cannot:
- Modify files directly
- Execute shell commands
- Make external API calls

This makes them safe for exploration and analysis tasks."""

SHELL_TOOLS_HELP = """# Shell Tools Guide

## Command Execution

### Basic Commands
```python
# Run simple commands
run_command(command="ls -la", cwd="/project")
run_command(command="git status")

# Run with environment variables
run_command(
    command="npm test",
    env={"NODE_ENV": "test", "CI": "true"}
)
```

### Bash Sessions
```python
# Use bash for session persistence
bash(command="cd /project && npm install")
bash(command="export API_KEY=test123 && npm run dev")
```

### Package Runners
```python
# Run Node packages
npx(package="prettier", args="--write src/**/*.js")
npx(package="create-react-app", args="my-app")

# Run Python packages
uvx(package="ruff", args="check .")
uvx(package="black", args="--check src/")
```

### Background Processes
```python
# Start long-running processes
run_command(command="npm run dev", background=True)

# Manage processes
process(action="list")  # List all background processes
process(action="logs", id="npm_abc123")  # View logs
process(action="kill", id="npm_abc123")  # Stop process
```

## Advanced Usage

### Batch Operations
```python
# Run multiple commands efficiently
batch(
    description="Run tests and linting",
    invocations=[
        {"tool_name": "run_command", "input": {"command": "npm test"}},
        {"tool_name": "run_command", "input": {"command": "npm run lint"}},
        {"tool_name": "run_command", "input": {"command": "npm audit"}}
    ]
)
```

### Working with Output
```python
# Capture and process output
result = run_command(command="git log --oneline -10")
# Process result.output for analysis
```

### Platform-Specific Commands
```python
# Open files/URLs in default application
open(path="https://github.com/user/repo")
open(path="/path/to/document.pdf")
```"""

BATCH_TOOL_EXAMPLES = """# Batch Tool Mastery

The batch tool is one of the most powerful features in Hanzo MCP, allowing parallel execution of multiple tools for maximum efficiency.

## Basic Batch Usage

```python
batch(
    description="Project setup",
    invocations=[
        {"tool_name": "run_command", "input": {"command": "npm install"}},
        {"tool_name": "run_command", "input": {"command": "pip install -r requirements.txt"}},
        {"tool_name": "directory_tree", "input": {"path": ".", "depth": 2}}
    ]
)
```

## Advanced Patterns

### 1. Parallel Search Operations
```python
batch(
    description="Find all authentication code",
    invocations=[
        {"tool_name": "grep", "input": {
            "pattern": "login|auth|session",
            "path": "/src"
        }},
        {"tool_name": "grep_ast", "input": {
            "pattern": "class.*Auth",
            "path": "/src"
        }},
        {"tool_name": "find", "input": {
            "pattern": "*auth*.py",
            "path": "/src"
        }}
    ]
)
```

### 2. Multi-Agent Analysis
```python
batch(
    description="Comprehensive code analysis",
    invocations=[
        {"tool_name": "dispatch_agent", "input": {
            "prompt": "Analyze code quality in /src/core modules"
        }},
        {"tool_name": "dispatch_agent", "input": {
            "prompt": "Review test coverage for /src/core modules"
        }},
        {"tool_name": "dispatch_agent", "input": {
            "prompt": "Identify performance bottlenecks in database operations"
        }}
    ]
)
```

### 3. File Operations
```python
batch(
    description="Read configuration files",
    invocations=[
        {"tool_name": "read_files", "input": {
            "paths": ["package.json", "tsconfig.json", ".env.example"]
        }},
        {"tool_name": "read_files", "input": {
            "paths": ["src/config/database.js", "src/config/auth.js"]
        }}
    ]
)
```

### 4. Complex Workflows
```python
# Step 1: Analyze
analysis_batch = batch(
    description="Analyze codebase",
    invocations=[
        {"tool_name": "grep", "input": {"pattern": "TODO|FIXME", "path": "."}},
        {"tool_name": "dispatch_agent", "input": {
            "prompt": "Find unused imports and dead code"
        }}
    ]
)

# Step 2: Based on analysis, perform fixes
fix_batch = batch(
    description="Fix identified issues",
    invocations=[
        {"tool_name": "content_replace", "input": {
            "pattern": "old_import",
            "replacement": "new_import",
            "path": "/src"
        }},
        {"tool_name": "run_command", "input": {"command": "npm run lint:fix"}}
    ]
)
```

## Batch Tool Best Practices

1. **Group Related Operations**: Batch operations that are logically related
2. **Maximize Parallelism**: Independent operations should be in the same batch
3. **Use Descriptive Names**: The description helps track what the batch does
4. **Handle Results**: Each tool result is returned in order

## Limitations

- Tools in a batch cannot depend on each other's results
- All tools run in parallel when possible
- Maximum efficiency with truly independent operations

## Available Tools for Batch

The following tools can be used in batch operations:
- dispatch_agent
- read_files
- directory_tree
- grep
- grep_ast
- run_command
- notebook_read
- find
- search_content
- symbols
- git_search

Tools NOT available in batch (require state/session):
- write_file
- edit_file
- multi_edit
- think
- todo_write"""


def create_tool_category_prompt(category: str, tools: list[str]):
    """Create a dynamic prompt for a specific tool category."""

    tool_descriptions = {
        "filesystem": FILESYSTEM_TOOLS_HELP,
        "agent": AGENT_TOOLS_HELP,
        "shell": SHELL_TOOLS_HELP,
        "batch": BATCH_TOOL_EXAMPLES,
    }

    base_prompt = tool_descriptions.get(category, f"# {category.title()} Tools\n\nAvailable tools in this category:\n")

    if category not in tool_descriptions:
        base_prompt += "\n".join(f"- **{tool}**: [Tool description]" for tool in tools)

    return base_prompt
