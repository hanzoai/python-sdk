# Hanzo Dev REPL - Usage Guide

## You're Connected! Now Here's How to Use It:

### Available Commands in the REPL:

```
help                - Show all available commands
status              - Show agent status
task <description>  - Execute a task
review <file>       - Review a code file
generate <desc>     - Generate code
debug <issue>       - Debug an issue
test <module>       - Generate tests
optimize <code>     - Optimize performance
exit                - Exit the REPL
```

### Example Usage:

```bash
hanzo-dev> status
Agent Status:
  primary: ready
  critic_1: ready

hanzo-dev> task review the Python files in this directory
[Agents will start reviewing...]

hanzo-dev> generate a simple REST API with FastAPI
[Agents will generate code...]

hanzo-dev> review src/main.py
[Agents will review the file...]

hanzo-dev> debug why is my server not starting
[Agents will help debug...]

hanzo-dev> test add unit tests for the user module
[Agents will generate tests...]
```

### How It Works:

1. **Primary Agent**: Handles main coding tasks
2. **Critic Agent**: Reviews and improves code (System 2 thinking)
3. **MCP Tools**: Both agents can use file operations, search, etc.
4. **Networking**: Agents can communicate with each other

### Quick Start Commands to Try:

```bash
# Check status
hanzo-dev> status

# Simple task
hanzo-dev> task list all Python files in the current directory

# Generate code
hanzo-dev> generate a hello world Flask app

# Review code
hanzo-dev> review README.md

# Get help
hanzo-dev> help
```

### Tips:

1. Use `task` for general requests
2. Use `generate` for creating new code
3. Use `review` for code review
4. Use `debug` for troubleshooting
5. Use `test` for test generation
6. Use `optimize` for performance improvements

### Advanced Usage:

```bash
# Multi-step task
hanzo-dev> task create a user authentication system with JWT tokens

# Code review with specific focus
hanzo-dev> review src/auth.py focus on security vulnerabilities

# Generate with requirements
hanzo-dev> generate REST API with CRUD operations for a blog system

# Debug with context
hanzo-dev> debug TypeError in line 42 of app.py when calling user.save()
```

### Exiting:

```bash
hanzo-dev> exit
Shutting down agents...
Goodbye!
```

## Troubleshooting:

If you see "Unknown command", make sure to:
1. Use one of the commands listed above
2. Start with a command word (task, generate, review, etc.)
3. Type `help` to see all available commands

## Example Session:

```bash
$ hanzo dev --orchestrator gpt-4

[... startup messages ...]

hanzo-dev> help
Available commands:
  help     - Show this help message
  status   - Show agent status
  task     - Execute a task
  review   - Review code
  generate - Generate code
  debug    - Debug issues
  test     - Generate tests
  optimize - Optimize code
  exit     - Exit REPL

hanzo-dev> status
Agents: 2 active (primary, critic_1)
MCP Tools: Enabled
Network: Connected

hanzo-dev> task explain what this project does
[Agents analyze the project...]
This project is a Python SDK for Hanzo AI that provides...

hanzo-dev> generate a simple calculator class
[Agents generate code...]
```python
class Calculator:
    def add(self, a, b):
        return a + b
    
    def subtract(self, a, b):
        return a - b
    
    def multiply(self, a, b):
        return a * b
    
    def divide(self, a, b):
        if b == 0:
            raise ValueError("Cannot divide by zero")
        return a / b
```

hanzo-dev> exit
✓ Agents shut down successfully
```