# hanzo-tools-vector

Vector search and embedding tools for Hanzo AI MCP.

## Tools

- `index` - Project indexing for semantic search
- `vector_index` - Create and manage vector embeddings
- `vector_search` - Semantic search across indexed content

## Installation

```bash
pip install hanzo-tools-vector

# With embedding models
pip install hanzo-tools-vector[full]
```

## Features

- Semantic code search
- Document embedding and retrieval
- Project-aware indexing
- Multiple embedding model support

## Usage

```python
from hanzo_tools.vector import TOOLS, VECTOR_AVAILABLE, register_tools

if VECTOR_AVAILABLE:
    register_tools(mcp_server, permission_manager)
```

## Part of hanzo-tools

This package is part of the modular [hanzo-tools](../hanzo-tools) ecosystem.
