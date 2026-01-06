# hanzo-tools-memory

Unified memory and knowledge management for AI agents. Store, recall, and manage memories and facts across sessions.

## Installation

```bash
pip install hanzo-tools-memory
```

Or as part of the full toolkit:

```bash
pip install hanzo-mcp[tools-all]
```

## Overview

`hanzo-tools-memory` provides:

- **Memory** - Episodic memory for storing and recalling information
- **Facts** - Knowledge base management for structured information
- **Scopes** - Session, project, and global memory levels
- **Summarization** - Automatic content summarization

## Quick Start

```python
# Store a memory
memory(action="create", data={"content": "User prefers dark mode"})

# Recall memories
memory(action="recall", query="user preferences")

# Store facts
memory(action="store_facts", data={
    "facts": ["API rate limit is 100/hour"],
    "kb_name": "api_docs"
})

# Recall facts
memory(action="facts", query="rate limit")
```

## Memory Actions

### create

Store new memories:

```python
memory(action="create", data={
    "content": "User prefers TypeScript over JavaScript",
    "scope": "project"  # session, project, or global
})

# Store multiple memories
memory(action="create", data={
    "statements": [
        "User works in Python",
        "Project uses FastAPI",
        "Prefers minimal dependencies"
    ]
})
```

### recall

Search and retrieve memories:

```python
# Simple query
memory(action="recall", query="user preferences")

# With scope filter
memory(action="recall", query="coding style", scope="project")

# Limit results
memory(action="recall", query="API endpoints", limit=5)

# Multiple queries (parallel search)
memory(action="recall", data={
    "queries": ["database schema", "API design", "error handling"]
})
```

### update

Modify existing memories:

```python
memory(action="update", data={
    "updates": [
        {"id": "mem_123", "statement": "User now prefers light mode"},
        {"id": "mem_456", "statement": "Updated API endpoint"}
    ]
})
```

### delete

Remove memories:

```python
memory(action="delete", data={
    "ids": ["mem_123", "mem_456"]
})
```

### manage

Batch operations (create, update, delete in one call):

```python
memory(action="manage", data={
    "creations": ["New fact 1", "New fact 2"],
    "updates": [{"id": "mem_1", "statement": "Updated"}],
    "deletions": ["mem_old1", "mem_old2"]
})
```

## Facts & Knowledge Bases

### store_facts

Store structured facts in knowledge bases:

```python
memory(action="store_facts", data={
    "facts": [
        "Python uses indentation for blocks",
        "FastAPI supports async/await"
    ],
    "kb_name": "python_basics",
    "scope": "project"
})
```

### facts

Query knowledge bases:

```python
# Query specific knowledge base
memory(action="facts", query="async patterns", kb_name="python_basics")

# Query all knowledge bases
memory(action="facts", query="error handling")

# With scope
memory(action="facts", query="API docs", scope="global")
```

### kb_manage

Manage knowledge bases:

```python
# Create knowledge base
memory(action="kb_manage", data={
    "action": "create",
    "kb_name": "api_docs",
    "description": "API documentation and endpoints"
})

# List knowledge bases
memory(action="kb_manage", data={"action": "list", "scope": "project"})

# Delete knowledge base
memory(action="kb_manage", data={"action": "delete", "kb_name": "old_docs"})
```

## Summarization

### summarize

Summarize content and store in memory:

```python
memory(action="summarize", data={
    "content": "Long discussion about API design decisions...",
    "topic": "API Design Decisions",
    "scope": "project",
    "auto_facts": True  # Auto-extract facts
})
```

## Scopes

Memories exist at three levels:

| Scope | Persistence | Use Case |
|-------|-------------|----------|
| `session` | Current session only | Temporary context |
| `project` | Per-project | Project-specific knowledge |
| `global` | All projects | User preferences, global facts |

```python
# Session memory (temporary)
memory(action="create", data={
    "content": "Currently debugging auth issue",
    "scope": "session"
})

# Project memory (persistent)
memory(action="create", data={
    "content": "Project uses PostgreSQL",
    "scope": "project"
})

# Global memory (shared)
memory(action="create", data={
    "content": "User prefers Vim keybindings",
    "scope": "global"
})
```

## Storage

Memories are stored in:

- `~/.hanzo/memory/session/` - Session memories
- `~/.hanzo/memory/project/<project>/` - Project memories
- `~/.hanzo/memory/global/` - Global memories

## Examples

### Context Building

```python
# At start of session, recall relevant context
memories = memory(action="recall", data={
    "queries": [
        "project architecture",
        "recent changes",
        "pending tasks"
    ],
    "scope": "project"
})
```

### Learning User Preferences

```python
# Store preference when learned
memory(action="create", data={
    "content": "User prefers functional programming style",
    "scope": "global"
})

# Later, recall preferences
prefs = memory(action="recall", query="coding style preferences")
```

### Project Documentation

```python
# Store project facts
memory(action="store_facts", data={
    "facts": [
        "Database: PostgreSQL 15",
        "ORM: SQLAlchemy 2.0",
        "API Framework: FastAPI",
        "Auth: JWT tokens"
    ],
    "kb_name": "tech_stack",
    "scope": "project"
})

# Query later
stack = memory(action="facts", query="what database", kb_name="tech_stack")
```

### Session Summarization

```python
# At end of session, summarize work
memory(action="summarize", data={
    "content": conversation_history,
    "topic": "Session Summary - Auth Implementation",
    "scope": "project"
})
```
