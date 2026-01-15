# Coding Standards

## Python Standards

### Code Formatting
- **Line Length**: 88 characters (Black default)
- **Imports**: Use isort with Black-compatible settings
- **Quotes**: Double quotes for strings, single quotes for string literals in code
- **Indentation**: 4 spaces, no tabs

### Naming Conventions
- **Variables/Functions**: snake_case (e.g., `user_name`, `calculate_total`)
- **Classes**: PascalCase (e.g., `UserManager`, `DatabaseConnection`)
- **Constants**: UPPER_SNAKE_CASE (e.g., `MAX_RETRY_ATTEMPTS`)
- **Private**: Leading underscore (e.g., `_internal_method`)

### Type Hints
- **Required**: All function signatures must have type hints
- **Return Types**: Always specify return types, use `None` for procedures
- **Generics**: Use generic types for containers (List[str], Dict[str, Any])
- **Optional**: Use `Optional[T]` for nullable parameters

```python
def process_data(
    items: List[Dict[str, Any]], 
    threshold: float = 0.5
) -> Optional[ProcessedData]:
    """Process data items with optional threshold."""
    pass
```

### Documentation
- **Docstrings**: Google style for all public functions and classes
- **Comments**: Explain why, not what (code should be self-documenting)
- **TODO/FIXME**: Include issue numbers when applicable

```python
def calculate_similarity(text1: str, text2: str) -> float:
    """Calculate semantic similarity between two texts.
    
    Args:
        text1: First text to compare
        text2: Second text to compare
        
    Returns:
        Similarity score between 0 and 1
        
    Raises:
        ValueError: If either text is empty
    """
    pass
```

### Error Handling
- **Specific Exceptions**: Catch specific exceptions, not bare `except:`
- **Error Messages**: Include context in error messages
- **Logging**: Log errors with appropriate levels
- **Recovery**: Implement graceful degradation when possible

```python
try:
    result = risky_operation()
except SpecificError as e:
    logger.error(f"Operation failed for {context}: {e}")
    raise ProcessingError(f"Cannot process {item_name}") from e
```

## JavaScript/TypeScript Standards

### Code Formatting
- **Tool**: Prettier with default settings
- **Semicolons**: Always use semicolons
- **Quotes**: Single quotes for strings, double quotes for JSX attributes
- **Trailing Commas**: Always include trailing commas

### Naming Conventions
- **Variables/Functions**: camelCase (e.g., `userName`, `calculateTotal`)
- **Classes**: PascalCase (e.g., `UserManager`, `DatabaseConnection`)
- **Constants**: UPPER_SNAKE_CASE (e.g., `MAX_RETRY_ATTEMPTS`)
- **Files**: kebab-case for components, camelCase for utilities

### TypeScript Specifics
- **Interfaces**: Use interfaces for object shapes
- **Types**: Use type aliases for unions and complex types
- **Strict Mode**: Enable strict TypeScript settings
- **Null Safety**: Use strict null checks

```typescript
interface UserData {
  id: string;
  name: string;
  email?: string;
}

type ProcessingResult = 'success' | 'failure' | 'pending';

function processUser(user: UserData): ProcessingResult {
  // Implementation
}
```

## SQL Standards

### Formatting
- **Keywords**: UPPERCASE for SQL keywords (SELECT, FROM, WHERE)
- **Names**: snake_case for table and column names
- **Indentation**: Align clauses and subqueries
- **Line Breaks**: One clause per line for complex queries

```sql
SELECT 
    u.id,
    u.name,
    COUNT(p.id) as post_count
FROM users u
LEFT JOIN posts p ON p.user_id = u.id
WHERE u.created_at > '2024-01-01'
GROUP BY u.id, u.name
ORDER BY post_count DESC;
```

### Design
- **Primary Keys**: Always use surrogate keys (id)
- **Foreign Keys**: Explicit foreign key constraints
- **Indexes**: Index foreign keys and frequently queried columns
- **Naming**: Consistent naming conventions

## Markdown Standards

### Structure
- **Headings**: Use ATX-style headers (#, ##, ###)
- **Lists**: Use dashes (-) for unordered lists
- **Code Blocks**: Always specify language for syntax highlighting
- **Links**: Use descriptive link text

### Organization
- **TOC**: Include table of contents for long documents
- **Sections**: Logical section organization with consistent depth
- **Examples**: Include code examples where relevant
- **Updates**: Track document updates with dates

## Git Standards

### Commit Messages
- **Format**: Conventional Commits (feat:, fix:, docs:, etc.)
- **Length**: 50 character summary, detailed description if needed
- **Imperative**: Use imperative mood ("Add feature" not "Added feature")

```
feat(memory): add hybrid markdown and SQLite storage

- Implement MemoryManager class with dual storage
- Add FTS5 support for full-text search  
- Include sqlite-vec integration for vector search
- Support both global and project-specific contexts

Closes #123
```

### Branching
- **Feature**: `feature/description` or `feature/issue-number`
- **Bugfix**: `fix/description` or `fix/issue-number`
- **Hotfix**: `hotfix/description`
- **Release**: `release/version`

---

*Last updated: 2025-01-12*
*Applies to: All Hanzo projects*