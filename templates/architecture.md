# Project Architecture Decisions

## Database Choice: Hybrid Memory System

**Date**: 2025-01-12  
**Status**: Implemented  
**Context**: Need for transparent, searchable memory management for AI agents

### Decision
Implemented hybrid memory system combining:
- **Plaintext markdown files** for human-readable rules and context
- **SQLite with FTS5** for full-text search across all content  
- **sqlite-vec extension** for vector similarity search
- **Layered search** across markdown + SQLite + vectors

### Rationale
- **Human-readable**: Markdown files can be edited with any text editor
- **Git-trackable**: Memory changes are version controlled
- **Searchable**: FTS5 provides fast full-text search without external dependencies
- **Semantic search**: sqlite-vec enables embedding-based similarity search
- **Portable**: Single-file databases per project, no external services
- **Standard**: Follows LLM.md pattern already established in the project

### Implementation
```
/project/
├── LLM.md                     # Project context (existing)
├── .hanzo/
│   ├── memory/                # Project memories  
│   │   ├── architecture.md   # This file
│   │   ├── patterns.md       # Code patterns
│   │   ├── decisions.md      # Technical decisions
│   │   └── sessions/         # Session logs
│   │       ├── 2025-01-12.md
│   │       └── 2025-01-13.md
│   └── db/
│       ├── project.db        # Existing project DB
│       ├── graph.db          # Existing graph DB  
│       └── memory.db         # New hybrid memory DB

~/.hanzo/
├── memory/                    # Global memories
│   ├── rules.md              # System rules
│   ├── user_preferences.md   # User preferences  
│   └── coding_standards.md   # Coding standards
└── db/
    └── global_memory.db      # Global memory DB
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

-- Full-text search indexes
CREATE VIRTUAL TABLE markdown_fts USING fts5(...);
CREATE VIRTUAL TABLE memories_fts USING fts5(...);

-- Vector embeddings (when sqlite-vec available)
CREATE TABLE embeddings (
    id INTEGER PRIMARY KEY,
    source_table TEXT NOT NULL,
    source_id INTEGER NOT NULL,
    embedding BLOB,
    model TEXT DEFAULT 'bge-small-en-v1.5'
);
```

### API Design
```python
# Unified memory tool with actions
memory(action="read", file_path="rules.md", scope="global")
memory(action="write", file_path="architecture.md", content="...", scope="project")
memory(action="append", file_path="sessions/today.md", content="New insight")
memory(action="search", content="database design", scope="both")
memory(action="create", content="Important fact", category="general")
memory(action="list", scope="project")
memory(action="stats")
```

### Benefits
1. **Transparency**: All memory storage is human-readable and editable
2. **Performance**: Local SQLite with FTS5 provides fast search
3. **Flexibility**: Supports both structured and unstructured data
4. **Portability**: No external dependencies, works offline
5. **Extensibility**: Can add vector search when embeddings are available

### Trade-offs
- **Complexity**: More complex than pure markdown or pure database approach
- **Storage**: Dual storage requires synchronization between files and database
- **Vector search**: Requires sqlite-vec extension installation

---

## Tool Architecture: Modular Package System

**Date**: 2024-12-01 (from LLM.md)  
**Status**: Implemented  
**Context**: Zero code duplication, dynamic tool discovery

### Decision
Modular tool package system with entry-point based discovery:
- `hanzo-mcp`: Thin wrapper that discovers tools via entry points
- `hanzo-tools-*`: Independent tool packages
- Dynamic loading without server restart

### Benefits
- **Zero duplication**: Tools live in single packages only
- **Modularity**: Install only needed tools
- **Dynamic**: Add/remove tools without restart
- **Maintainability**: Clear separation of concerns

---

## Memory Integration Strategy

**Date**: 2025-01-12  
**Status**: In Progress  

### Phase 1: Add hybrid memory alongside existing system
- ✓ Implement MemoryManager class
- ✓ Create MemoryTool with unified actions  
- ✓ Add to hanzo-tools-database package
- ✓ Support markdown + SQLite + FTS5

### Phase 2: Enhanced integration  
- [ ] Add vector embedding generation (FastEmbed integration)
- [ ] Implement sqlite-vec vector search
- [ ] Auto-append to session memories from think/critic tools
- [ ] Template system for common memory structures

### Phase 3: Migration from existing memory system
- [ ] Import important memories from hanzo-memory package
- [ ] Provide migration tools for existing vector data
- [ ] Deprecate complex LiteLLM/InfinityDB system

### Phase 4: Full optimization
- [ ] Keep SQLite for structured data (file metadata, symbols, graph)
- [ ] Markdown for rules/context, SQLite for search performance
- [ ] Vector search for semantic similarity when available

---

*This file tracks major architectural decisions for the project.*  
*Add new decisions with date, status, context, and rationale.*