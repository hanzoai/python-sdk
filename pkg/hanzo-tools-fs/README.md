# hanzo-tools-fs

Filesystem tools for Hanzo MCP.

## Installation

```bash
pip install hanzo-tools-fs
```

## Tools

### read - Read Files
```python
read(file_path="/path/to/file.py")
read(file_path="/path/to/file.py", offset=100, limit=50)
```

### write - Write Files
```python
write(file_path="/path/to/file.py", content="...")
```

### edit - Edit Files
```python
edit(
    file_path="/path/to/file.py",
    old_string="def old():",
    new_string="def new():"
)
```

### tree - Directory Structure
```python
tree(path="/project", depth=3)
```

### find - File Discovery
```python
find(pattern="*.py", path="/project")
```

### search - Content Search
```python
search(pattern="TODO|FIXME", path="./src")
```

### ast - Code Structure
```python
ast(pattern="class.*Service", path="/src")
```

## License

MIT
