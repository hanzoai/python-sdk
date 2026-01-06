# hanzo-tools-todo

Task management tools for tracking progress and organizing work.

## Installation

```bash
pip install hanzo-tools-todo
```

Or as part of the full toolkit:

```bash
pip install hanzo-mcp[tools-all]
```

## Overview

`hanzo-tools-todo` provides task management:

- **todo** - Unified task management with list, add, update, remove, clear operations

## Quick Start

```python
# List all todos
todo()
todo(action="list")

# Add a new todo
todo(action="add", content="Fix the authentication bug")

# Update status
todo(action="update", id="abc123", status="in_progress")

# Mark complete
todo(action="update", id="abc123", status="completed")

# Remove a todo
todo(action="remove", id="abc123")

# Clear all todos
todo(action="clear")
```

## Actions Reference

### list

List all todos, optionally filtered by status.

```python
# List all
todo(action="list")

# Filter by status
todo(action="list", filter="pending")
todo(action="list", filter="in_progress")
todo(action="list", filter="completed")
```

**Response:**
```json
{
  "todos": [
    {"id": "abc123", "content": "Fix bug", "status": "in_progress", "priority": "high"},
    {"id": "def456", "content": "Write tests", "status": "pending", "priority": "medium"}
  ],
  "count": 2
}
```

### add

Add a new todo item.

```python
# Simple add
todo(action="add", content="Implement feature X")

# With priority
todo(action="add", content="Critical fix", priority="high")

# With status
todo(action="add", content="Already started", status="in_progress")
```

**Parameters:**
- `content` (required): Todo description
- `status`: Initial status - "pending" (default), "in_progress", "completed"
- `priority`: Priority level - "low", "medium" (default), "high"

### update

Update an existing todo.

```python
# Update status
todo(action="update", id="abc123", status="completed")

# Update content
todo(action="update", id="abc123", content="Updated description")

# Update priority
todo(action="update", id="abc123", priority="high")
```

**Parameters:**
- `id` (required): Todo ID
- `content`: New content
- `status`: New status
- `priority`: New priority

### remove

Remove a todo by ID.

```python
todo(action="remove", id="abc123")
```

### clear

Clear all todos.

```python
todo(action="clear")
```

## Status Workflow

```
pending → in_progress → completed
    ↑_________|  (can go back if needed)
```

**Statuses:**
- `pending` - Not yet started
- `in_progress` - Currently being worked on
- `completed` - Finished

## Priority Levels

- `high` - Urgent, do first
- `medium` - Normal priority (default)
- `low` - Can wait

## Storage

Todos are stored per-session in memory. For persistent todos, use the memory tools to save to disk.

## Examples

### Project Workflow

```python
# Add tasks for a feature
todo(action="add", content="Design API schema", priority="high")
todo(action="add", content="Implement endpoints", priority="high")
todo(action="add", content="Write tests", priority="medium")
todo(action="add", content="Update documentation", priority="low")

# Start working
todo(action="update", id="<design_id>", status="in_progress")

# Complete and move on
todo(action="update", id="<design_id>", status="completed")
todo(action="update", id="<implement_id>", status="in_progress")
```

### Tracking Progress

```python
# Check what's in progress
todo(action="list", filter="in_progress")

# Check what's pending
todo(action="list", filter="pending")

# Check completed
todo(action="list", filter="completed")
```

## Best Practices

1. **Use meaningful descriptions** - Clear content helps tracking
2. **Set appropriate priorities** - High for blockers, medium for features
3. **Update status promptly** - Keep todos current
4. **Clear completed items** - Periodically clean up finished tasks
