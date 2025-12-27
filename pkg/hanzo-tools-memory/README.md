# hanzo-tools-memory

Memory and knowledge management tools for Hanzo MCP.

## Installation

```bash
pip install hanzo-tools-memory
```

## Tools

### memory - Unified Memory Management
Single tool with multiple actions for memory operations.

**Recall memories:**
```python
memory(action="recall", query="project architecture")
memory(action="recall", queries=["user preferences", "coding standards"])
```

**Create memories:**
```python
memory(action="create", data={"content": "User prefers dark mode"})
memory(action="create", statements=["Fact 1", "Fact 2"])
```

**Update memories:**
```python
memory(action="update", id="mem_123", statement="Updated fact")
```

**Delete memories:**
```python
memory(action="delete", ids=["mem_123", "mem_456"])
```

**Knowledge bases:**
```python
memory(action="facts", query="API endpoints", kb_name="api_docs")
memory(action="store", facts=["Rate limit: 100/hour"], kb_name="api_docs")
memory(action="kb", action_type="list")  # List knowledge bases
```

**Summarize:**
```python
memory(
    action="summarize",
    content="Long discussion about API design...",
    topic="API Design Decisions"
)
```

## Scopes

- `session` - Current session only
- `project` - Project-specific (default)
- `global` - Across all projects

## License

MIT
