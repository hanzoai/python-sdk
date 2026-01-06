# hanzo-aci

Agent-Computer Interface (ACI) designed for software development agents.

## Installation

```bash
pip install hanzo-aci
```

## Overview

hanzo-aci provides a comprehensive interface for AI agents to interact with codebases, enabling:

- **Code Understanding** - AST parsing with tree-sitter
- **Repository Analysis** - Git integration and file operations
- **Semantic Search** - Code search and pattern matching
- **Diff Generation** - Create and apply patches

## Features

### AST Parsing

Parse code into abstract syntax trees using tree-sitter:

```python
from dev_aci import parse_code

# Parse Python code
ast = parse_code("""
def hello(name: str) -> str:
    return f"Hello, {name}!"
""", language="python")

# Get functions
functions = ast.get_functions()
for func in functions:
    print(f"{func.name}: {func.line_number}")
```

### Supported Languages

| Language | tree-sitter Package |
|----------|---------------------|
| Python | `tree-sitter-python` |
| JavaScript | `tree-sitter-javascript` |
| TypeScript | `tree-sitter-typescript` |
| Ruby | `tree-sitter-ruby` |

### Repository Analysis

Work with Git repositories:

```python
from dev_aci import Repository

# Open repository
repo = Repository("/path/to/repo")

# Get file tree
tree = repo.get_tree()

# Get file content
content = repo.read_file("src/main.py")

# Get recent changes
changes = repo.get_recent_commits(limit=10)

# Search for patterns
matches = repo.search("TODO")
```

### Code Search

Find code patterns:

```python
from dev_aci import CodeSearch

search = CodeSearch("/path/to/repo")

# Search by pattern
results = search.find_pattern("class.*Service")

# Search by function name
funcs = search.find_functions("handle_*")

# Search by reference
refs = search.find_references("MyClass")
```

### Diff Operations

Generate and apply patches:

```python
from dev_aci import DiffGenerator

diff = DiffGenerator()

# Generate diff
patch = diff.create_patch(
    original="def foo(): pass",
    modified="def foo():\n    return 42",
)

# Apply patch
result = diff.apply_patch(content, patch)
```

## Configuration

### Dependencies

hanzo-aci includes these dependencies:

- **numpy, pandas, scipy** - Data processing
- **networkx** - Graph analysis
- **litellm** - LLM integration
- **gitpython** - Git operations
- **tree-sitter** - AST parsing
- **grep-ast** - Code search

### Optional Dependencies

```bash
# Development tools
pip install hanzo-aci[dev]

# Testing tools
pip install hanzo-aci[test]
```

## Usage Examples

### Agent Code Understanding

```python
from dev_aci import Repository, CodeSearch

async def understand_codebase(repo_path: str):
    repo = Repository(repo_path)
    search = CodeSearch(repo_path)

    # Get structure
    tree = repo.get_tree()

    # Find entry points
    main_files = search.find_pattern("if __name__ == .__main__.")

    # Find tests
    test_files = search.find_functions("test_*")

    return {
        "structure": tree,
        "entry_points": main_files,
        "test_files": test_files,
    }
```

### Code Modification Agent

```python
from dev_aci import Repository, DiffGenerator, parse_code

async def modify_code(repo_path: str, file_path: str, modification: str):
    repo = Repository(repo_path)
    diff = DiffGenerator()

    # Read original
    original = repo.read_file(file_path)

    # Parse and understand
    ast = parse_code(original, language="python")

    # Generate modification
    modified = apply_modification(original, modification)

    # Create patch
    patch = diff.create_patch(original, modified)

    return patch
```

### Code Review Agent

```python
from dev_aci import Repository, CodeSearch, parse_code

async def review_code(repo_path: str, file_path: str):
    repo = Repository(repo_path)

    # Get file content
    content = repo.read_file(file_path)

    # Parse AST
    ast = parse_code(content, language="python")

    # Analyze
    issues = []

    # Check function length
    for func in ast.get_functions():
        if func.line_count > 50:
            issues.append(f"Function {func.name} is too long ({func.line_count} lines)")

    # Check for TODOs
    search = CodeSearch(repo_path)
    todos = search.find_pattern("TODO|FIXME", file=file_path)
    if todos:
        issues.append(f"Found {len(todos)} TODO/FIXME comments")

    return issues
```

## API Reference

### Repository

| Method | Description |
|--------|-------------|
| `get_tree()` | Get file tree structure |
| `read_file(path)` | Read file content |
| `write_file(path, content)` | Write file content |
| `get_recent_commits(limit)` | Get recent commits |
| `search(pattern)` | Search repository |

### CodeSearch

| Method | Description |
|--------|-------------|
| `find_pattern(pattern)` | Search by regex pattern |
| `find_functions(pattern)` | Find function definitions |
| `find_classes(pattern)` | Find class definitions |
| `find_references(name)` | Find symbol references |

### DiffGenerator

| Method | Description |
|--------|-------------|
| `create_patch(original, modified)` | Generate diff patch |
| `apply_patch(content, patch)` | Apply patch to content |
| `validate_patch(patch)` | Validate patch format |

### AST Functions

| Function | Description |
|----------|-------------|
| `parse_code(code, language)` | Parse code into AST |
| `get_functions()` | Get function definitions |
| `get_classes()` | Get class definitions |
| `get_imports()` | Get import statements |

## Best Practices

1. **Use AST for Analysis**: Prefer AST over regex for code analysis
2. **Cache Repositories**: Reuse Repository instances for efficiency
3. **Validate Patches**: Always validate patches before applying
4. **Handle Errors**: Code parsing can fail - handle ParseError exceptions
5. **Language Detection**: Use file extensions to detect language automatically
