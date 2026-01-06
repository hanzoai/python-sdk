# Database Tools

The database tools (`hanzo-tools-database`) provide SQL and graph database operations for project-embedded databases.

## Overview

Each project can have an embedded SQLite database with tables for metadata, files, and symbols. The database tools also support graph database operations for tracking code relationships.

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
```

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

### 3. Index Before Querying

Ensure the project is indexed before running database queries:

```python
# Index project first
index(path="/project")

# Then query
sql_query(query="SELECT * FROM symbols WHERE type='function'")
```
