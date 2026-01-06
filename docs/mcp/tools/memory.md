# Memory Tools

Persistent memory and knowledge base management.

→ **Full documentation: [../../tools/memory.md](../../tools/memory.md)**

## Quick Reference

```python
# Recall memories
recall_memories(queries=["project architecture"])

# Create memories
create_memories(statements=["User prefers dark mode"])

# Store facts
store_facts(facts=["API rate limit: 100/hour"], kb_name="api_docs")

# Recall facts
recall_facts(queries=["rate limits"], kb_name="api_docs")

# Summarize to memory
summarize_to_memory(content="...", topic="Architecture Decisions")

# Manage knowledge bases
manage_knowledge_bases(action="create", kb_name="docs", description="Project docs")
```

9 tools for memory and knowledge management.
