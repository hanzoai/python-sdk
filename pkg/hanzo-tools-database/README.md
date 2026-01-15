# Hanzo Database Tools

Hybrid memory management system combining plaintext markdown files, SQLite full-text search, and optional vector similarity search.

## Features

🗂️ **Hybrid Storage**
- **Markdown files**: Human-readable rule files (git-trackable)
- **SQLite FTS5**: Fast full-text search with ranking and snippets  
- **Vector search**: Semantic similarity via sqlite-vec extension

🔍 **Unified Search**
- Search across markdown files and structured memories
- Full-text search with relevance ranking
- Optional vector similarity search for semantic queries

📊 **Project & Global Scope**
- Global memories: `~/.hanzo/memory/` (system rules, preferences)
- Project memories: `project/.hanzo/memory/` (architecture, patterns)
- Session memories: Daily logs and insights

## Quick Start

### Installation

```bash
# Basic installation
pip install hanzo-tools-database

# With vector search (optional)
pip install hanzo-tools-database[vector]
python setup_sqlite_vec.py
```

### Usage

```python
# Read global rules
memory(action="read", file_path="rules.md", scope="global")

# Write project architecture
memory(action="write", file_path="architecture.md", content="# Architecture...", scope="project")

# Append to session log
memory(action="append", file_path="sessions/today.md", content="Important insight")

# Search all memories
memory(action="search", content="database design", scope="both")

# Create structured memory
memory(action="create", content="Key decision", category="architecture", importance=8)

# List and stats
memory(action="list", scope="project")
memory(action="stats")
```

## Architecture

### Storage Structure
```
~/.hanzo/
├── memory/                     # Global memories
│   ├── rules.md               # System rules
│   ├── user_preferences.md    # User preferences
│   └── coding_standards.md    # Coding standards
└── db/
    └── global_memory.db       # Global search index

/project/
├── .hanzo/
│   ├── memory/                # Project memories
│   │   ├── architecture.md   # Decisions
│   │   ├── patterns.md       # Code patterns
│   │   └── sessions/         # Daily logs
│   └── db/
│       ├── project.db        # Project data
│       ├── graph.db          # Code graph
│       └── memory.db         # Memory index
```

### Database Schema
```sql
-- Markdown files index
CREATE TABLE markdown_files (
    id INTEGER PRIMARY KEY,
    path TEXT NOT NULL UNIQUE,
    content TEXT NOT NULL,
    category TEXT,
    scope TEXT CHECK(scope IN ('global', 'project')),
    modified_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Structured memories
CREATE TABLE memories (
    id INTEGER PRIMARY KEY,
    content TEXT NOT NULL,
    category TEXT,
    importance INTEGER DEFAULT 5,
    metadata TEXT, -- JSON
    scope TEXT CHECK(scope IN ('global', 'project', 'session')),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- FTS5 indexes
CREATE VIRTUAL TABLE markdown_fts USING fts5(...);
CREATE VIRTUAL TABLE memories_fts USING fts5(...);

-- Vector embeddings (optional)
CREATE TABLE embeddings (
    id INTEGER PRIMARY KEY,
    source_table TEXT NOT NULL,
    source_id INTEGER NOT NULL,
    embedding BLOB,
    model TEXT DEFAULT 'bge-small-en-v1.5'
);
```

## Memory Tool Actions

| Action | Description | Parameters |
|--------|-------------|------------|
| `read` | Read markdown file | `file_path`, `scope` |
| `write` | Write markdown file | `file_path`, `content`, `scope`, `category` |
| `append` | Append with timestamp | `file_path`, `content`, `scope` |
| `search` | Search all memories | `content` (query), `scope`, `search_type`, `limit` |
| `create` | Create structured memory | `content`, `category`, `importance`, `scope` |
| `list` | List memory files | `scope` |
| `stats` | Get system statistics | `scope` |

## sqlite-vec Vector Search

### Setup
```bash
# Install sqlite-vec extension
python setup_sqlite_vec.py

# Verify installation
python -c "
import sqlite3
conn = sqlite3.connect(':memory:')
conn.enable_load_extension(True) 
conn.load_extension('vec0')
print('✓ sqlite-vec available')
"
```

### Features
- **Semantic search**: Find conceptually similar content
- **Embedding models**: BGE, sentence-transformers, custom models
- **Efficient storage**: Binary vectors in SQLite
- **Fast queries**: Optimized similarity search

### Usage
```python
# Enable vector search
memory(action="search", content="api design", search_type="vector", scope="both")

# Hybrid search (text + vectors)
memory(action="search", content="database patterns", search_type="hybrid", scope="project")
```

## SQL & Graph Tools

### SQL Operations
```python
# Execute queries
sql_query(query="SELECT * FROM files WHERE type='python'")

# Search with FTS
sql_search(pattern="TODO", table="files")

# Get statistics  
sql_stats()
```

### Graph Operations
```python
# Add relationships
graph_add(source="main.py", target="utils.py", relationship="imports")

# Query graph
graph_query(query="neighbors", node_id="main.py")

# Search nodes
graph_search(pattern="Service", node_type="class")

# Get stats
graph_stats()
```

## Best Practices

### 1. Memory Organization
- **Global scope**: System rules, user preferences, coding standards
- **Project scope**: Architecture decisions, patterns, specific context
- **Session scope**: Daily logs, temporary insights, work progress

### 2. File Structure
- Use descriptive file names: `architecture.md`, `api_design.md`
- Organize sessions by date: `sessions/2025-01-12.md`
- Use categories for structured memories: `architecture`, `patterns`, `decisions`

### 3. Search Strategy
- **Text search**: Use `fulltext` for exact term matching
- **Semantic search**: Use `vector` for conceptual similarity (requires sqlite-vec)
- **Hybrid search**: Combine text and vectors for best results

### 4. Performance
- Index regularly with FTS5 for fast search
- Use appropriate scopes to limit search space
- Set reasonable limits for large result sets

## Development

### Testing
```bash
# Run test suite
python test_memory_system.py

# Test specific features
python -c "from hanzo_tools.database import MemoryManager; print('✓ Import successful')"
```

### Contributing
1. Follow existing patterns in `memory_manager.py` and `memory_tool.py`
2. Add tests for new features
3. Update documentation for API changes
4. Ensure backward compatibility

## Migration

### From hanzo-memory
The new system can coexist with the existing `hanzo-memory` package:
- Phase 1: Use hybrid system for new memories
- Phase 2: Gradually migrate important memories to markdown
- Phase 3: Deprecate complex vector database system
- Phase 4: Keep SQLite for structured data, markdown for context

### Benefits vs. Current System
- **Simpler**: No complex LiteLLM/InfinityDB dependencies
- **Transparent**: Human-readable markdown files
- **Portable**: Single-file SQLite databases per project
- **Git-friendly**: Memory changes are version controlled
- **Standard**: Follows LLM.md pattern for AI context

---

**Part of Hanzo AI Python SDK**: https://github.com/hanzoai/python-sdk
