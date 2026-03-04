# hanzo-tools-memory

Memory and knowledge management tools for Hanzo MCP.

## Installation

```bash
pip install hanzo-tools-memory
```

## Tools

### memory - Memory Management
Single tool surface with action-based operations.

**Recall memories:**
```python
memory(action="recall", query="project architecture")
memory(action="recall", queries=["user preferences", "coding standards"])
```

**Create memories:**
```python
memory(action="create", content="User prefers dark mode")
```

**Update memories:**
```python
memory(action="update", id="mem_123", content="Updated fact")
```

**Delete memories:**
```python
memory(action="delete", ids=["mem_123", "mem_456"])
```

**Knowledge bases:**
```python
memory(action="facts", query="API endpoints", kb="api_docs")
memory(action="store", facts=["Rate limit: 100/hour"], kb="api_docs")
memory(action="kb", kb_action="list")  # List knowledge bases
```

**Summarize:**
```python
memory(
    action="summarize",
    content="Long discussion about API design...",
    tags=["api", "design"]
)
```

**Backend selection (optional):**
```python
memory(action="recall", query="project auth flow", backend="auto")   # local-first (default)
memory(action="recall", query="project auth flow", backend="local")  # markdown only
memory(action="recall", query="project auth flow", backend="cloud")  # cloud/vector only
memory(action="recall", query="project auth flow", backend="hybrid") # local + cloud
```

## Scopes

- `session` - Current session only
- `project` - Project-specific (default)
- `global` - Across all projects

## License

MIT
