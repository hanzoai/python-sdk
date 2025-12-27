# hanzo-tools-todo

Task management tools for Hanzo MCP.

## Installation

```bash
pip install hanzo-tools-todo
```

## Tools

### todo - Task Management
Manage todo items with status tracking.

**List todos:**
```python
todo()  # List all
todo(filter="in_progress")  # Filter by status
```

**Add todo:**
```python
todo(action="add", content="Implement feature X")
todo(action="add", content="Critical bug", priority="high")
```

**Update todo:**
```python
todo(action="update", id="abc123", status="completed")
todo(action="update", id="abc123", content="Updated description")
```

**Remove todo:**
```python
todo(action="remove", id="abc123")
todo(action="clear")  # Remove all
```

## Status Values

- `pending` - Not started
- `in_progress` - Currently working
- `completed` - Done

## Priority Values

- `high` - Urgent
- `medium` - Normal (default)
- `low` - Can wait

## License

MIT
