# Filesystem Tools

File operations with AST analysis.

→ **Full documentation: [../../tools/fs.md](../../tools/fs.md)**

## Quick Reference

```python
# Read file
read(file_path="/path/to/file.py")

# Write file
write(file_path="/path/to/file.py", content="...")

# Edit file
edit(file_path="/path/to/file.py", old_string="old", new_string="new")

# Directory tree
tree(path="/project", depth=3)

# Find files
find(pattern="*.py", path="/src")

# Search content
search(pattern="TODO", path=".")

# AST analysis
ast(pattern="def test_", path="/tests")
```

7 tools: `read`, `write`, `edit`, `tree`, `find`, `search`, `ast`
