# Database Tools

The database tools (`hanzo-tools-database`) provide SQL, graph database, and hybrid memory operations for project-embedded databases.

## Overview

Each project can have embedded SQLite databases with support for:
- **SQL operations** with tables for metadata, files, and symbols
- **Graph database** operations for tracking code relationships  
- **Hybrid memory system** combining markdown files + SQLite + vector search

## Memory Tool - Hybrid Storage

### Unified Memory Management

The `memory` tool provides a hybrid storage system that combines:
- **Plaintext markdown files** for human-readable rules/context
- **SQLite with FTS5** for full-text search across all content
- **sqlite-vec extension** for vector similarity search (optional)
- **Layered search** across all storage types

### File Structure
```
~/.hanzo/                           # Global hanzo config
├── memory/                         # Global memories
│   ├── rules.md                   # Global rules/context  
│   ├── user_preferences.md        # User preferences
│   └── coding_standards.md        # Coding standards
└── db/
    └── global_memory.db           # Global memory database

/path/to/project/                   # Project-specific
├── LLM.md                         # Project context (existing)
├── .hanzo/
│   ├── memory/                    # Project memories
│   │   ├── architecture.md       # Architecture decisions
│   │   ├── patterns.md            # Code patterns
│   │   └── sessions/              # Session memories
│   │       ├── 2025-01-12.md     # Daily sessions
│   │       └── 2025-01-13.md
│   └── db/
│       ├── project.db            # Existing project DB
│       ├── graph.db              # Existing graph DB
│       └── memory.db             # Hybrid memory DB
```

### Memory Tool Usage

```python
# Read memory files
memory(action="read", file_path="rules.md", scope="global")
memory(action="read", file_path="architecture.md", scope="project")

# Write memory files
memory(action="write", file_path="patterns.md", content="# Code Patterns...", scope="project")

# Append to session logs
memory(action="append", file_path="sessions/today.md", content="New insight about the codebase")

# Search across all memories
memory(action="search", content="database design", scope="both", limit=10)

# Create structured memories
memory(action="create", content="Important architectural decision", category="architecture", importance=8)

# List memory files  
memory(action="list", scope="project")

# Get statistics
memory(action="stats")
```

#### Memory Actions

| Action | Description | Parameters |
|--------|-------------|------------|
| `read` | Read markdown memory file | `file_path`, `scope` |
| `write` | Write markdown memory file | `file_path`, `content`, `scope`, `category` |
| `append` | Append to markdown file with timestamp | `file_path`, `content`, `scope` |
| `search` | Search across all memory types | `content` (query), `scope`, `search_type`, `limit` |
| `create` | Create structured memory record | `content`, `category`, `importance`, `scope` |  
| `list` | List all memory files | `scope` |
| `stats` | Get memory system statistics | `scope` |

#### Parameters

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `action` | str | `search` | Memory action to perform |
| `content` | str | - | Content to store or search query |
| `file_path` | str | - | Markdown file path (e.g., 'rules.md', 'sessions/today.md') |
| `category` | str | - | Memory category for organization |
| `scope` | str | `project` | Memory scope: global, project, or both |
| `search_type` | str | `fulltext` | Search type: fulltext, vector, or hybrid |
| `importance` | int | 5 | Memory importance (1-10) |
| `limit` | int | 10 | Maximum results to return |

### Features

#### Full-Text Search (FTS5)
- Fast text search across markdown files and structured memories
- Snippet highlighting with search terms marked
- Ranking by relevance score

#### Vector Search (sqlite-vec)
- Semantic similarity search using embeddings
- Requires sqlite-vec extension (install with `python setup_sqlite_vec.py`)
- Support for BGE and other embedding models

#### Layered Storage
- **Markdown files**: Human-readable, git-trackable, editable
- **SQLite index**: Fast search and metadata storage
- **Vector embeddings**: Semantic similarity (when available)

## SQL Tools

### sql_query - Execute SQL Queries

Execute raw SQL on the project database:

```python
# Read query (default safe mode)
sql_query(query="SELECT * FROM files LIMIT 10")

# Query with specific project
sql_query(query="SELECT name, type FROM symbols WHERE type='function'", project_path="/project")

# Write query (requires read_only=False)
sql_query(
    query="INSERT INTO metadata (key, value) VALUES ('version', '1.0')",
    read_only=False
)
```

#### Parameters

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `query` | str | required | SQL query to execute |
| `project_path` | str | cwd | Project path |
| `read_only` | bool | `True` | Block write operations |

#### Database Schema

Default tables in project databases:

```sql
-- Key-value metadata
CREATE TABLE metadata (
    key TEXT PRIMARY KEY,
    value TEXT
);

-- File information
CREATE TABLE files (
    path TEXT PRIMARY KEY,
    content TEXT,
    modified_at TEXT
);

-- Code symbols
CREATE TABLE symbols (
    id INTEGER PRIMARY KEY,
    name TEXT,
    type TEXT,  -- function, class, variable
    file_path TEXT,
    line_number INTEGER
);
```

### sql_search - Full-Text Search

Search database content with text matching:

```python
sql_search(pattern="error", table="files")
sql_search(pattern="TODO", column="content")
```

### sql_stats - Database Statistics

Get database statistics and schema info:

```python
sql_stats()
sql_stats(project_path="/project")
```

## Graph Tools

The graph database stores relationships between code entities (files, functions, classes).

### graph_add - Add Nodes/Edges

Add nodes and edges to the graph:

```python
# Add a node
graph_add(node_id="main.py", node_type="file")

# Add an edge
graph_add(
    source="main.py",
    target="utils.py",
    relationship="imports"
)

# Add with properties
graph_add(
    node_id="MyClass",
    node_type="class",
    properties={"methods": 5, "lines": 120}
)
```

### graph_remove - Remove from Graph

Remove nodes or edges:

```python
graph_remove(node_id="deprecated_file.py")
graph_remove(source="a.py", target="b.py", relationship="imports")
```

### graph_query - Query Graph Database

Execute graph traversal queries:

```python
# Find neighbors
graph_query(query="neighbors", node_id="main.py")

# Find path between nodes
graph_query(query="path", node_id="main.py", target_id="utils.py")

# Get subgraph
graph_query(query="subgraph", node_id="MyClass", depth=3)

# Find ancestors (nodes pointing TO this node)
graph_query(query="ancestors", node_id="error_handler", relationship="calls")

# Find descendants (nodes this node points TO)
graph_query(query="descendants", node_id="BaseClass", relationship="inherits")

# Find all connected nodes
graph_query(query="connected", node_id="main.py", direction="both")
```

#### Query Types

| Query | Description | Required Params |
|-------|-------------|-----------------|
| `neighbors` | Direct neighbors | `node_id` |
| `path` | Shortest path | `node_id`, `target_id` |
| `subgraph` | Subgraph around node | `node_id` |
| `connected` | All connected nodes | `node_id` |
| `ancestors` | Incoming edges | `node_id` |
| `descendants` | Outgoing edges | `node_id` |

#### Parameters

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `query` | str | required | Query type |
| `node_id` | str | - | Starting node |
| `target_id` | str | - | Target node (for path) |
| `depth` | int | `2` | Max traversal depth |
| `relationship` | str | - | Filter by edge type |
| `node_type` | str | - | Filter by node type |
| `direction` | str | `both` | `both`, `incoming`, `outgoing` |

### graph_search - Search Graph

Search for nodes by properties:

```python
graph_search(pattern="Service", node_type="class")
graph_search(pattern="test_*", relationship="depends_on")
```

### graph_stats - Graph Statistics

Get graph statistics:

```python
graph_stats()
# Returns: nodes count, edges count, relationship types, node types
```

## Relationship Types

Common relationship types in code graphs:

| Relationship | Description |
|--------------|-------------|
| `imports` | File imports another file |
| `calls` | Function calls another function |
| `inherits` | Class inherits from another |
| `implements` | Class implements interface |
| `depends_on` | General dependency |
| `contains` | File contains symbol |

## Installation

```bash
pip install hanzo-tools-database

# For vector search support
pip install hanzo-tools-database[vector]
python -m hanzo_tools.database.setup_sqlite_vec
```

## sqlite-vec Vector Search Setup

The sqlite-vec extension provides vector similarity search capabilities:

```bash
# Install sqlite-vec extension
cd pkg/hanzo-tools-database
python setup_sqlite_vec.py

# Test installation
python -c "
import sqlite3
conn = sqlite3.connect(':memory:')
conn.enable_load_extension(True)
conn.load_extension('vec0')
print('✓ sqlite-vec is available')
"
```

### Vector Search Features
- **Semantic similarity**: Find conceptually similar content
- **Embedding models**: Support for BGE, sentence-transformers, etc.
- **Efficient storage**: Binary vector storage in SQLite
- **Fast queries**: Optimized vector similarity search

## Best Practices

### 1. Use Read-Only Mode

```python
# Default: safe read-only queries
sql_query(query="SELECT * FROM files")

# Only disable when necessary
sql_query(query="UPDATE ...", read_only=False)
```

### 2. Filter Graph Queries

```python
# Avoid unbounded traversals
graph_query(query="subgraph", node_id="main.py", depth=2)

# Filter by relationship type
graph_query(query="neighbors", node_id="func", relationship="calls")
```

### 3. Organize Memories

```python
# Use clear categories
memory(action="create", content="API design decision", category="architecture")

# Use session logs for temporal organization
memory(action="append", file_path="sessions/2025-01-12.md", content="Today's insights")

# Keep global rules for system-wide context
memory(action="write", file_path="rules.md", scope="global", content="System guidelines")
```

### 4. Index Before Querying

Ensure the project is indexed before running database queries:

```python
# Index project first
index(path="/project")

# Then query
sql_query(query="SELECT * FROM symbols WHERE type='function'")
```

### 5. Memory Initialization

Initialize memory structure for new projects:

```python
# Initialize global memory (run once per user)
python -m hanzo_tools.database.init_memory

# Initialize project memory (run once per project)  
cd /path/to/project
python -m hanzo_tools.database.init_memory .
```
