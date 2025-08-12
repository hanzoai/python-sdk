"""Enhanced prompts for better discoverability and usability."""

QUICK_START_PROMPT = """# Hanzo MCP Quick Start Guide

## Common Workflows

### 1. Explore a New Codebase
```python
# Get project overview
directory_tree(path=".", depth=3)

# Find main entry points
find(pattern="main.*|index.*", path=".")

# Search for key patterns
search(pattern="TODO|FIXME|BUG", path=".")
```

### 2. Multi-Agent Code Analysis
```python
# Run parallel analysis with different agents
batch(
    description="Comprehensive code analysis",
    invocations=[
        {"tool_name": "agent", "input": {"prompt": "Analyze security vulnerabilities"}},
        {"tool_name": "agent", "input": {"prompt": "Find performance bottlenecks"}},
        {"tool_name": "agent", "input": {"prompt": "Review code quality and suggest improvements"}}
    ]
)
```

### 3. Refactor Code Across Files
```python
# Find all occurrences
search(pattern="oldFunction", path="./src")

# Review with critic
critic(analysis="Review the usage of oldFunction and suggest refactoring approach")

# Make changes
content_replace(
    pattern="oldFunction",
    replacement="newFunction",
    path="./src"
)

# Run tests
bash("npm test")
```

### 4. Track Complex Tasks
```python
# Create todo list
todo_write(todos=[
    {"content": "Analyze current implementation", "status": "pending"},
    {"content": "Design new architecture", "status": "pending"},
    {"content": "Implement changes", "status": "pending"},
    {"content": "Write tests", "status": "pending"},
    {"content": "Update documentation", "status": "pending"}
])

# Update as you work
todo(action="update", id="task-1", status="completed")
```

## Tips
- Use `batch()` for parallel operations
- Use `think()` for complex reasoning
- Use `critic()` for code review
- Use pagination for large result sets"""

PAGINATION_GUIDE_PROMPT = """# Pagination Guide

## How Pagination Works

Most tools support pagination to handle large result sets efficiently.

### Basic Pagination Parameters
- `page`: Page number (starts at 1)
- `page_size`: Results per page (default: 50-100)
- `max_results`: Total maximum results

### Examples

#### Find Tool with Pagination
```python
# Get first page of Python files
find(pattern="*.py", path="/project", page=1, page_size=10)

# Response includes:
{
  "results": [...],
  "pagination": {
    "page": 1,
    "page_size": 10,
    "total_results": 150,
    "total_pages": 15,
    "has_next": true,
    "has_prev": false
  }
}

# Get next page
find(pattern="*.py", path="/project", page=2, page_size=10)
```

#### Search with Limits
```python
# Limit total results
search(pattern="TODO", path="/project", max_results=20)
```

### Batch Processing Pages
```python
# Process multiple pages in parallel
batch(
    description="Get all Python files",
    invocations=[
        {"tool_name": "find", "input": {"pattern": "*.py", "page": 1, "page_size": 50}},
        {"tool_name": "find", "input": {"pattern": "*.py", "page": 2, "page_size": 50}},
        {"tool_name": "find", "input": {"pattern": "*.py", "page": 3, "page_size": 50}}
    ]
)
```

## Best Practices
1. Start with smaller page sizes for testing
2. Use `max_results` to limit total processing
3. Check `has_next` before requesting next page
4. Use batch for parallel page fetching"""

MEMORY_VECTOR_HELP_PROMPT = """# Memory & Vector Tools Guide

## Semantic Search and Memory

### Vector Search
Search using semantic similarity rather than exact text matching.

```python
# Enable vector search in unified search
search(
    pattern="how to handle user authentication",
    path="/project",
    enable_vector=true
)

# Index project for vector search
vector_index(path="/project", recursive=true)

# Pure vector search
vector_search(
    query="error handling patterns",
    path="/project",
    top_k=10
)
```

### Memory Tools
Store and retrieve context across sessions.

```python
# Store knowledge
memory_add(
    key="project_architecture",
    content="The project uses a microservices architecture with..."
)

# Retrieve knowledge
memory_get(key="project_architecture")

# Search memory
memory_search(query="architecture decisions")
```

## Use Cases
1. **Semantic Code Search**: Find conceptually similar code
2. **Knowledge Base**: Store project understanding
3. **Context Preservation**: Maintain context across sessions
4. **Pattern Discovery**: Find similar implementations

## Tips
- Index large projects once, search many times
- Combine vector search with traditional search
- Use memory for important discoveries
- Vector search works best with natural language queries"""

DATABASE_TOOLS_HELP_PROMPT = """# Database Tools Guide

## SQL Database Operations

### Query Execution
```python
# Execute SQL query
sql_query(
    query="SELECT * FROM users WHERE created_at > '2024-01-01'",
    database="myapp.db"
)

# Search across tables
sql_search(
    pattern="john@example.com",
    database="myapp.db"
)

# Get database statistics
sql_stats(database="myapp.db")
```

## Graph Database Operations

### Managing Graph Data
```python
# Add nodes and edges
graph_add(
    node_type="User",
    node_id="user_123",
    properties={"name": "John", "email": "john@example.com"}
)

graph_add(
    edge_type="FOLLOWS",
    from_node="user_123",
    to_node="user_456"
)

# Query graph
graph_query(
    query="MATCH (u:User)-[:FOLLOWS]->(f:User) RETURN u, f",
    database="social.graph"
)

# Search graph
graph_search(
    pattern="John",
    node_type="User"
)

# Graph statistics
graph_stats(database="social.graph")
```

## Best Practices
1. Always sanitize inputs to prevent injection
2. Use transactions for multiple operations
3. Index frequently queried fields
4. Monitor query performance with stats tools"""

LSP_TOOLS_HELP_PROMPT = """# Language Server Protocol (LSP) Tools Guide

## Code Intelligence Features

### Basic Operations
```python
# Go to definition
lsp(
    action="definition",
    file="/src/main.py",
    line=42,
    character=15
)

# Find all references
lsp(
    action="references",
    file="/src/main.py",
    line=42,
    character=15
)

# Get hover information
lsp(
    action="hover",
    file="/src/main.py",
    line=42,
    character=15
)
```

### Refactoring
```python
# Rename symbol across codebase
lsp(
    action="rename",
    file="/src/main.py",
    line=42,
    character=15,
    new_name="newFunctionName"
)
```

### Diagnostics
```python
# Get errors and warnings
lsp(
    action="diagnostics",
    file="/src/main.py"
)
```

### Code Completion
```python
# Get completions at position
lsp(
    action="completion",
    file="/src/main.py",
    line=42,
    character=15
)
```

## Supported Languages
- Python (pylsp)
- TypeScript/JavaScript (typescript-language-server)
- Go (gopls)
- Rust (rust-analyzer)
- Java (jdtls)
- C/C++ (clangd)

## Tips
- LSP servers are installed automatically
- Use for accurate refactoring
- Combine with search tools for comprehensive analysis"""

CONFIGURATION_GUIDE_PROMPT = """# Configuration Guide

## Tool Configuration

### View Current Configuration
```python
# List all enabled tools
tool_list()

# Check specific tool status
stats()
```

### Enable/Disable Tools
```python
# Enable a tool
tool_enable(name="lsp")

# Disable a tool
tool_disable(name="sql_query")
```

## Configuration Presets

### Available Presets

1. **minimal** - Essential tools only
   - Basic file operations
   - Simple commands
   
2. **standard** - Common development tools
   - File operations
   - Search tools
   - Process management
   
3. **development** - Full development suite
   - All standard tools
   - Agent tools
   - Package managers
   - LSP support
   
4. **full** - Everything enabled
   - All tools available
   - Maximum capabilities
   
5. **ai_research** - AI/ML focused
   - Agent orchestration
   - Vector search
   - Memory tools

### Switching Presets
Configure in your launch command:
```bash
# Use development preset
hanzo-mcp --preset development

# Or set in config file
~/.config/hanzo/mcp-settings.json
```

## Environment Variables
```bash
# Agent configuration
export HANZO_AGENT_MODEL="openai/gpt-4"
export HANZO_API_KEY="your-key"

# Tool settings
export HANZO_COMMAND_TIMEOUT=300
export HANZO_ENABLE_AGENT_TOOL=true
```

## Project-Specific Config
Create `.hanzo/config.json` in your project:
```json
{
  "enabled_tools": ["lsp", "vector_search"],
  "disabled_tools": ["sql_query"],
  "agent": {
    "model": "claude-3-sonnet",
    "max_iterations": 15
  }
}
```"""

NETWORK_AGENT_GUIDE_PROMPT = """# Network Agent Orchestration Guide

## Distributed AI Processing

The `network` tool (also accessible as `swarm` for compatibility) enables distributed AI workloads across multiple agents.

### Basic Multi-Agent Setup
```python
# Launch parallel agents
network(
    task="Analyze this codebase for security, performance, and quality",
    agents=["security_expert", "performance_analyst", "code_reviewer"],
    mode="parallel"
)
```

### Execution Modes

#### 1. Local Mode (Privacy-First)
```python
network(
    task="Process sensitive data",
    mode="local",  # Uses only local compute
    agents=["data_processor", "analyzer"]
)
```

#### 2. Distributed Mode
```python
network(
    task="Large-scale analysis",
    mode="distributed",  # Uses network resources
    agents=["agent1", "agent2", "agent3"]
)
```

#### 3. Hybrid Mode (Default)
```python
network(
    task="General processing",
    mode="hybrid",  # Local first, cloud fallback
    agents=["primary", "secondary"]
)
```

### Routing Strategies

#### Sequential Processing
```python
network(
    task="Multi-step workflow",
    agents=["preprocessor", "analyzer", "reporter"],
    routing="sequential"  # Each agent processes in order
)
```

#### Parallel Processing
```python
network(
    task="Independent analyses",
    agents=["test_runner", "linter", "security_scan"],
    routing="parallel"  # All agents work simultaneously
)
```

#### Consensus Decision
```python
network(
    task="Critical decision",
    agents=["expert1", "expert2", "expert3"],
    routing="consensus"  # Agents must agree
)
```

### Claude CLI Integration
```python
# Run multiple Claude instances in parallel
batch(
    description="Parallel Claude analysis",
    invocations=[
        {"tool_name": "claude_cli", "input": {"prompt": "Review architecture"}},
        {"tool_name": "claude_cli", "input": {"prompt": "Analyze performance"}},
        {"tool_name": "claude_cli", "input": {"prompt": "Check security"}}
    ]
)
```

## Advanced Features
- **MCP Connections**: Agents communicate via MCP protocol
- **State Sharing**: Agents share context and memory
- **Tool Sharing**: Agents can use each other's tools
- **Recursive Calling**: Agents can spawn sub-agents

## Best Practices
1. Use local mode for sensitive data
2. Use parallel routing for independent tasks
3. Use consensus for critical decisions
4. Monitor agent resource usage"""

PERFORMANCE_TIPS_PROMPT = """# Performance Optimization Guide

## Speed Optimization

### 1. Use Batch for Parallel Operations
```python
# SLOW - Sequential execution
result1 = read(file="/file1.py")
result2 = read(file="/file2.py")
result3 = read(file="/file3.py")

# FAST - Parallel execution
batch(
    description="Read multiple files",
    invocations=[
        {"tool_name": "read", "input": {"file_path": "/file1.py"}},
        {"tool_name": "read", "input": {"file_path": "/file2.py"}},
        {"tool_name": "read", "input": {"file_path": "/file3.py"}}
    ]
)
```

### 2. Use Unified Search
```python
# Combines multiple search methods efficiently
search(
    pattern="important_function",
    path="/project",
    max_results=20
)
```

### 3. Limit Result Sets
```python
# Use pagination
find(pattern="*.py", page=1, page_size=50)

# Set max results
grep(pattern="TODO", max_results=100)
```

### 4. Use Appropriate Tools
```python
# For code structure - use AST search
grep_ast(pattern="class.*Service", path="/src")

# For exact text - use grep
grep(pattern="ERROR:", path="/logs")

# For concepts - use vector search
vector_search(query="authentication flow", path="/src")
```

## Memory Optimization

### 1. Process Large Files in Chunks
```python
# Read with offset and limit
read(file="/large_file.log", offset=1000, limit=100)
```

### 2. Use Streaming for Long Operations
```python
# Background long-running processes
bash("npm run dev", background=true)

# Check status separately
process(action="list")
```

## Network Optimization

### 1. Local-First Processing
```python
# Use local compute when possible
network(task="analyze", mode="local")
```

### 2. Cache Results
```python
# Index once, search many times
vector_index(path="/project")
# Now searches are fast
vector_search(query="pattern", use_cache=true)
```

## Tips
- Profile before optimizing
- Use batch for I/O operations
- Limit data transferred
- Use appropriate search methods
- Cache expensive operations"""

SECURITY_BEST_PRACTICES_PROMPT = """# Security Best Practices

## Safe Tool Usage

### 1. Path Validation
```python
# Always use absolute paths from known locations
read(file="/home/user/project/file.py")  # Good
read(file="../../../etc/passwd")  # Blocked

# Tools validate paths against allowed directories
```

### 2. Command Injection Prevention
```python
# Use parameterized commands
bash(f"grep {pattern} file.txt")  # Risky if pattern is user input

# Better: Use dedicated tools
grep(pattern=user_input, path="file.txt")  # Safe
```

### 3. Sensitive Data Handling
```python
# Never log sensitive data
think("Processing user data [REDACTED]")

# Use local mode for sensitive operations
network(
    task="Process PII data",
    mode="local",  # Stays on device
    require_local=true
)
```

## Permission Management

### 1. Tool Permissions
- Read operations are generally safe
- Write operations require confirmation
- System commands are restricted

### 2. Agent Permissions
```python
# Agents inherit permission restrictions
agent(
    prompt="Analyze code",
    permissions=["read", "search"]  # Limited permissions
)
```

## Data Protection

### 1. Local Processing
```python
# Keep data local
network(mode="local", task="Process confidential data")
```

### 2. Secure Communication
- All MCP connections use secure channels
- Agent communications are encrypted
- No data persisted without permission

## Best Practices
1. Validate all inputs
2. Use least privilege principle
3. Keep sensitive data local
4. Audit tool usage
5. Review agent outputs
6. Don't execute untrusted code
7. Use sandboxed environments for testing"""

TROUBLESHOOTING_GUIDE_PROMPT = """# Troubleshooting Guide

## Common Issues and Solutions

### 1. Tool Not Found
```
Error: Tool 'X' not found
```
**Solution:**
```python
# Check if tool is enabled
tool_list()

# Enable if needed
tool_enable(name="tool_name")
```

### 2. Permission Denied
```
Error: Permission denied for path X
```
**Solution:**
- Ensure path is in allowed directories
- Launch with: `hanzo-mcp --allow-path /your/path`

### 3. Timeout Errors
```
Error: Command timed out
```
**Solution:**
```python
# Increase timeout
bash("long_command", timeout=300)

# Or run in background
bash("long_command", background=true)
```

### 4. Memory Issues
```
Error: Result too large
```
**Solution:**
```python
# Use pagination
find(pattern="*", page=1, page_size=50)

# Limit results
grep(pattern="text", max_results=100)

# Read in chunks
read(file="/large.txt", offset=0, limit=1000)
```

### 5. Agent Failures
```
Error: Agent failed to complete task
```
**Solution:**
```python
# Increase iterations
agent(
    prompt="task",
    max_iterations=20,
    max_tool_uses=50
)

# Use simpler prompts
# Break complex tasks into steps
```

### 6. Network Issues
```
Error: Cannot connect to cluster
```
**Solution:**
```python
# Use local mode
network(mode="local", task="...")

# Check cluster status
mcp_stats()
```

## Debugging Tips

### 1. Enable Verbose Output
```python
# Get detailed information
stats()

# Check process status
process(action="list")

# View logs
process(action="logs", id="process_id")
```

### 2. Test Incrementally
```python
# Start simple
read(file="/test.txt")

# Then expand
batch(invocations=[...])
```

### 3. Check Documentation
```python
# View help for specific category
"/hanzo:Filesystem tools help"
"/hanzo:Agent tools help"

# Explore all tools
"/hanzo:Explore all tools"
```

## Getting Help
1. Check error messages carefully
2. Use `think()` to reason about issues
3. Consult category-specific help
4. Try simpler alternatives
5. Report persistent issues"""

# Export all prompts
__all__ = [
    "QUICK_START_PROMPT",
    "PAGINATION_GUIDE_PROMPT",
    "MEMORY_VECTOR_HELP_PROMPT",
    "DATABASE_TOOLS_HELP_PROMPT",
    "LSP_TOOLS_HELP_PROMPT",
    "CONFIGURATION_GUIDE_PROMPT",
    "NETWORK_AGENT_GUIDE_PROMPT",
    "PERFORMANCE_TIPS_PROMPT",
    "SECURITY_BEST_PRACTICES_PROMPT",
    "TROUBLESHOOTING_GUIDE_PROMPT",
]
