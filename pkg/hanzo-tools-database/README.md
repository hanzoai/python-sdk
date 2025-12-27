# hanzo-tools-database

Database tools for Hanzo MCP.

## Installation

```bash
pip install hanzo-tools-database
```

## Tools

### SQL Tools

**sql_query:**
```python
sql_query(query="SELECT * FROM users WHERE active = true")
```

**sql_search:**
```python
sql_search(table="users", pattern="john%")
```

**sql_stats:**
```python
sql_stats(table="users")  # Table statistics
```

### Graph Database Tools

**graph_add:**
```python
graph_add(node_type="Person", properties={"name": "John", "age": 30})
graph_add(
    edge_type="KNOWS",
    from_node="person_1",
    to_node="person_2"
)
```

**graph_remove:**
```python
graph_remove(node_id="person_1")
```

**graph_query:**
```python
graph_query(pattern="MATCH (p:Person) RETURN p")
```

**graph_search:**
```python
graph_search(node_type="Person", properties={"name": "John"})
```

**graph_stats:**
```python
graph_stats()  # Graph statistics
```

## Configuration

Set database URLs via environment:

```bash
DATABASE_URL=postgresql://user:pass@localhost:5432/db
GRAPH_DATABASE_URL=neo4j://localhost:7687
```

## License

MIT
