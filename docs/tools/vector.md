# Vector Tools

The vector tools (`hanzo-tools-vector`) provide semantic search capabilities using vector embeddings and the Infinity embedded database.

## Overview

These tools enable indexing documents and searching by semantic similarity rather than keyword matching. Perfect for finding conceptually related content.

## Installation

```bash
# Basic install
pip install hanzo-tools-vector

# Full install with all dependencies
pip install hanzo-tools-vector[full]
```

## index - Project Indexing

Index project files for search:

```python
# Index current project
index(path=".")

# Index specific directory
index(path="/project/src")

# Index with file filter
index(path=".", include="*.py,*.md")

# Re-index (force update)
index(path=".", force=True)
```

### Parameters

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `path` | str | `.` | Directory to index |
| `include` | str | - | File patterns to include |
| `exclude` | str | - | File patterns to exclude |
| `force` | bool | `False` | Force re-indexing |

## vector_index - Document Indexing

Add documents to the vector index:

```python
# Index a single document
vector_index(
    content="This is the document content...",
    file_path="/docs/guide.md"
)

# Index with metadata
vector_index(
    content="API documentation...",
    file_path="/docs/api.md",
    metadata={"category": "api", "version": "2.0"}
)

# Index multiple documents
vector_index(
    documents=[
        {"content": "Doc 1...", "file_path": "/a.md"},
        {"content": "Doc 2...", "file_path": "/b.md"}
    ]
)
```

### Parameters

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `content` | str | - | Document content |
| `file_path` | str | - | Source file path |
| `metadata` | dict | - | Additional metadata |
| `documents` | list | - | Batch of documents |

## vector_search - Semantic Search

Search indexed documents by meaning:

```python
# Basic semantic search
vector_search(query="How do I authenticate users?")

# Search with limit
vector_search(query="error handling patterns", limit=5)

# Search with score threshold
vector_search(query="database optimization", score_threshold=0.7)

# Search specific project
vector_search(query="API endpoints", search_scope="my-project")

# Filter by file pattern
vector_search(query="testing patterns", file_filter="test_*.py")

# Search all projects
vector_search(query="configuration", search_scope="all")
```

### Parameters

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `query` | str | required | Search query |
| `limit` | int | `10` | Max results to return |
| `score_threshold` | float | `0.0` | Min similarity score (0-1) |
| `include_content` | bool | `True` | Include document content |
| `file_filter` | str | - | Filter by file path pattern |
| `project_filter` | list | - | Filter by project names |
| `search_scope` | str | `all` | `all`, `global`, `current`, or project name |

### Search Scopes

| Scope | Description |
|-------|-------------|
| `all` | Search all indexed projects |
| `global` | Search only global index |
| `current` | Search current project (auto-detected) |
| `<name>` | Search specific project by name |

### Output Format

```
Found 3 results for query: 'authentication patterns'

Result 1 (Score: 87.3%) - Project: my-api - src/auth/handler.py [Chunk 2]
------------------------------------------------------------------
Metadata: {"category": "auth"}
Content:
def authenticate_user(token: str) -> User:
    """Authenticate user from JWT token..."""
    ...

Result 2 (Score: 82.1%) - Project: my-api - docs/auth.md [Chunk 0]
------------------------------------------------------------------
Content:
# Authentication Guide

This guide explains how to authenticate users...
```

## How It Works

### Embedding Generation

Documents are converted to vector embeddings that capture semantic meaning:

1. **Chunking**: Large documents split into smaller chunks
2. **Embedding**: Each chunk converted to vector representation
3. **Storage**: Vectors stored in Infinity database
4. **Indexing**: HNSW index for fast similarity search

### Similarity Search

Queries are embedded and compared against document vectors:

1. **Query Embedding**: Convert query to vector
2. **Nearest Neighbors**: Find most similar document vectors
3. **Scoring**: Calculate similarity scores (0-1)
4. **Ranking**: Return top results by score

## Project Detection

Projects are automatically detected by looking for `LLM.md` files:

```
/home/user/projects/
├── project-a/
│   ├── LLM.md          <- Project root detected
│   └── src/
├── project-b/
│   ├── LLM.md          <- Project root detected
│   └── lib/
```

Each project gets its own isolated vector index.

## Best Practices

### 1. Index Before Searching

```python
# Initial indexing
index(path="/project")

# Then search
vector_search(query="your query")
```

### 2. Use Appropriate Score Thresholds

```python
# High precision (fewer results, more relevant)
vector_search(query="...", score_threshold=0.8)

# High recall (more results, some noise)
vector_search(query="...", score_threshold=0.5)
```

### 3. Combine with Keyword Search

```python
# Semantic search for concepts
vector_search(query="error handling best practices")

# Keyword search for exact matches
grep(pattern="raise ValueError")
```

### 4. Filter by File Type

```python
# Search only documentation
vector_search(query="setup instructions", file_filter="*.md")

# Search only code
vector_search(query="authentication", file_filter="*.py")
```

### 5. Use Project Scope for Speed

```python
# Faster: search specific project
vector_search(query="...", search_scope="my-project")

# Slower: search all projects
vector_search(query="...", search_scope="all")
```

## Comparison: Vector vs Keyword Search

| Feature | vector_search | grep |
|---------|---------------|------|
| Match type | Semantic similarity | Exact text pattern |
| Finds synonyms | Yes | No |
| Requires indexing | Yes | No |
| Speed (large corpus) | Fast (indexed) | Slower |
| Best for | Concepts, questions | Exact code, identifiers |

Example:

```python
# Semantic search finds conceptually related content
vector_search(query="how to handle errors")
# Finds: exception handling, try/catch blocks, error recovery

# Keyword search finds exact patterns
grep(pattern="except Exception")
# Finds: only lines with "except Exception"
```
