# Hanzo MCP Search Guide

## Overview

Hanzo MCP provides a powerful unified search system that intelligently combines multiple search modalities to help you find anything in your codebase. The system consists of two primary tools:

1. **Unified Search** (`search`) - THE primary search interface that finds everything
2. **Find Tool** (`find`) - Fast file and directory discovery

## Unified Search Tool

The unified search tool is your universal interface for finding:
- Code patterns and text matches (using ripgrep)
- AST nodes and code structure (using treesitter)
- Symbol definitions and references (using ctags/LSP)
- Files and directories (using find tool)
- Memory and knowledge base entries
- Semantic/conceptual matches (using vector search)

### Key Features

- **Intelligent Query Detection**: Automatically determines the best search strategy based on your query
- **Parallel Search**: Runs multiple search types concurrently for speed
- **Deduplication**: Removes duplicate results across search types
- **Relevance Ranking**: Sorts results by relevance and match quality
- **Context Awareness**: Provides surrounding context for matches
- **Pagination**: Handles large result sets efficiently

### Usage Examples

#### 1. Find Code Patterns
```python
# Find all error handling code
search("error handling")

# Find TODOs and FIXMEs (regex)
search("TODO|FIXME")

# Find async functions
search("async function")
```

#### 2. Find Symbols/Definitions
```python
# Find a class definition
search("class UserService")

# Find a function/method
search("handleRequest")

# Find a constant
search("MAX_RETRIES")
```

#### 3. Find Files
```python
# Find test files
search("test_*.py", search_files=True)

# Find config files
search("config", search_files=True)
```

#### 4. Semantic Search
```python
# Natural language queries
search("how authentication works")
search("database connection logic")
search("error handling patterns")
```

#### 5. Memory Search
```python
# Search previous discussions
search("previous discussion about API design")
search("that bug we fixed last week")
```

### Advanced Usage

#### Filtering Results
```python
# Search only in Python files
search("import requests", include="*.py")

# Exclude test files
search("DatabaseConnection", exclude="*test*")

# Search in specific directory
search("TODO", path="src/services")
```

#### Controlling Search Types
```python
# Force specific search types
search("pattern",
    enable_text=True,      # Text search (always on)
    enable_ast=True,       # AST search
    enable_vector=True,    # Semantic search
    enable_symbol=True,    # Symbol search
    search_files=True,     # File name search
    search_memory=True     # Memory search
)
```

#### Pagination
```python
# Get first page of results
result = search("async", page_size=20, page=1)

# Get next page
if result.data["pagination"]["has_next"]:
    result = search("async", page_size=20, page=2)
```

### How It Works

1. **Query Analysis**: The tool analyzes your query to determine intent
   - Code syntax → Text/AST/Symbol search
   - Natural language → Vector/semantic search
   - Glob patterns → File search

2. **Parallel Execution**: Appropriate search types run concurrently

3. **Result Processing**:
   - Deduplication across search types
   - Relevance scoring based on:
     - Match type (exact > fuzzy)
     - Location (definitions > usage)
     - File type (source > test > vendor)
   - Context extraction

4. **Presentation**: Results are formatted with previews and context

## Find Tool

The find tool is optimized for quickly finding files and directories by name, pattern, or attributes.

### Key Features

- **Lightning Fast**: Uses `ffind` when available for blazing performance
- **Smart Pattern Matching**: Supports glob, regex, and fuzzy matching
- **File Attribute Filtering**: Filter by size, modification time, type
- **Human-Readable**: Sizes and times in readable format
- **Gitignore Aware**: Respects .gitignore by default

### Usage Examples

#### Basic File Finding
```python
# Find all Python files
find("*.py")

# Find files starting with test_
find("test_", type="file")

# Find directories named src
find("src", type="dir")
```

#### Advanced Filtering
```python
# Find large files (>10MB)
find("*", min_size="10MB")

# Find recently modified files
find("*", modified_after="1 day ago")

# Find old log files
find("*.log", modified_before="1 week ago")

# Find files in size range
find("*", min_size="1MB", max_size="10MB")
```

#### Pattern Matching Options
```python
# Regex pattern matching
find(r"test_\w+\.py", regex=True)

# Fuzzy matching (typo-tolerant)
find("confg", fuzzy=True)  # Finds "config" files

# Case-sensitive search
find("README", case_sensitive=True)
```

#### Performance Options
```python
# Limit search depth
find("*.js", max_depth=3)

# Don't follow symlinks
find("*", follow_symlinks=False)

# Include gitignored files
find("*", respect_gitignore=False)

# Sort results
find("*.py", sort_by="size", reverse=True)
```

## Integration with Other Tools

### AST-Aware Multi-Edit

The new AST-aware multi-edit tool can use the unified search to find all references before making changes:

```python
# Find and rename a function across the codebase
ast_multi_edit("main.go", [
    {
        "old_string": "ProcessData",
        "new_string": "ProcessDataWithContext",
        "semantic_match": True,  # Find all references
        "node_types": ["call_expression"]  # Only function calls
    }
])
```

### LSP Tool

The LSP tool provides language-specific intelligence:

```python
# Check if Go LSP is available
lsp("status", file="main.go")

# Find definition (uses LSP when available)
lsp("definition", file="app.py", line=42, character=10)

# Find all references
lsp("references", file="service.ts", line=15, character=5)

# Rename symbol
lsp("rename", file="lib.rs", line=20, character=8, new_name="new_name")
```

## Search Strategies

### For Maximum Coverage

Use the unified search tool - it automatically runs all appropriate search types:

```python
# This will search text, AST, symbols, vectors, and more
search("authentication flow")
```

### For Speed

1. **Known file names**: Use the find tool
   ```python
   find("config.json")
   ```

2. **Specific text**: Use grep directly
   ```python
   grep("TODO")
   ```

3. **Code structure**: Use ast tool (symbols)
   ```python
   symbols("function.*process")
   ```

### For Accuracy

1. **Symbol definitions**: Enable symbol search
   ```python
   search("MyClass", enable_symbol=True)
   ```

2. **Semantic meaning**: Enable vector search
   ```python
   search("how to handle errors", enable_vector=True)
   ```

3. **Exact matches**: Use regex anchors
   ```python
   search("^class MyClass$")
   ```

## Performance Tips

1. **Use specific paths** when you know the general location:
   ```python
   search("pattern", path="src/services")
   ```

2. **Limit results** for faster response:
   ```python
   search("common_term", max_results_per_type=10)
   ```

3. **Use appropriate page sizes**:
   ```python
   # Smaller pages for interactive use
   search("pattern", page_size=20)
   
   # Larger pages for batch processing
   search("pattern", page_size=100)
   ```

4. **Exclude unnecessary files**:
   ```python
   search("pattern", exclude="node_modules,*.min.js")
   ```

## Configuration

### Vector Search Setup

To enable semantic/vector search:

1. Install dependencies:
   ```bash
   pip install chromadb sentence-transformers
   ```

2. The tool will automatically initialize vector search when available

3. Build index for better performance:
   ```python
   # This happens automatically on first use
   # But can be triggered manually for large codebases
   ```

### LSP Configuration

The LSP tool automatically installs language servers as needed. Supported languages:

- **Go**: gopls
- **Python**: python-lsp-server
- **TypeScript/JavaScript**: typescript-language-server  
- **Rust**: rust-analyzer
- **Java**: jdtls
- **C/C++**: clangd
- **Ruby**: solargraph
- **Lua**: lua-language-server

## Troubleshooting

### Search Returns Too Many Results

1. Be more specific in your query
2. Use filters (include/exclude)
3. Limit search types
4. Reduce max_results_per_type

### Search is Slow

1. Use specific paths instead of searching entire codebase
2. Disable vector search for simple text searches
3. Use find tool for file discovery
4. Install ripgrep for faster text search

### Missing Expected Results

1. Check if files are gitignored
2. Verify file permissions
3. Try different search types
4. Use more general patterns

### Vector Search Not Working

1. Check if chromadb is installed
2. Verify sentence-transformers is available
3. Check for initialization errors in logs
4. Try rebuilding the index

## Best Practices

1. **Start with unified search** - it's the most comprehensive
2. **Use natural language** for conceptual searches
3. **Use code syntax** for exact matches
4. **Combine search types** for best results
5. **Review statistics** to understand what was searched
6. **Use pagination** for large result sets
7. **Cache results** when doing multiple related searches

## Summary

The Hanzo MCP search system provides a powerful, intelligent way to find anything in your codebase. The unified search tool should be your primary interface, automatically selecting the best search strategies for your queries. The find tool complements this with ultra-fast file discovery.

Together, these tools ensure you can quickly locate any code, file, symbol, or concept in your project, making development more efficient and enjoyable.