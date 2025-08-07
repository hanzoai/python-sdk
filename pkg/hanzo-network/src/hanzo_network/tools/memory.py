"""Memory tools for agents using the hanzo-memory package."""

from typing import Any, Dict, List, Optional
from dataclasses import dataclass

from .core.tool import Tool, create_tool, ToolContext

# Import from hanzo-memory package when available
try:
    from hanzo_memory import MemoryStore, VectorStore
    MEMORY_AVAILABLE = True
except ImportError:
    MEMORY_AVAILABLE = False
    MemoryStore = None
    VectorStore = None


@dataclass
class MemoryManager:
    """Manager for agent memory operations."""
    
    def __init__(self, store_type: str = "vector", **kwargs):
        """Initialize memory manager.
        
        Args:
            store_type: Type of store (vector, graph, etc.)
            **kwargs: Store-specific configuration
        """
        if not MEMORY_AVAILABLE:
            raise ImportError("hanzo-memory package not available")
        
        if store_type == "vector":
            self.store = VectorStore(**kwargs)
        else:
            self.store = MemoryStore(**kwargs)
    
    async def recall(self, queries: List[str], limit: int = 10) -> List[Dict[str, Any]]:
        """Recall memories matching queries.
        
        Args:
            queries: Search queries
            limit: Max results per query
            
        Returns:
            List of matching memories
        """
        results = []
        
        for query in queries:
            matches = await self.store.search(query, limit=limit)
            results.extend(matches)
        
        # Deduplicate by ID
        seen = set()
        unique_results = []
        for result in results:
            if result.get("id") not in seen:
                seen.add(result.get("id"))
                unique_results.append(result)
        
        return unique_results
    
    async def create(self, statements: List[str]) -> List[str]:
        """Create new memories.
        
        Args:
            statements: Memory statements to store
            
        Returns:
            List of created memory IDs
        """
        ids = []
        
        for statement in statements:
            memory_id = await self.store.add({
                "content": statement,
                "type": "statement"
            })
            ids.append(memory_id)
        
        return ids
    
    async def update(self, updates: List[Dict[str, str]]) -> List[bool]:
        """Update existing memories.
        
        Args:
            updates: List of {id, statement} dicts
            
        Returns:
            List of success flags
        """
        results = []
        
        for update in updates:
            success = await self.store.update(
                update["id"],
                {"content": update["statement"]}
            )
            results.append(success)
        
        return results
    
    async def delete(self, ids: List[str]) -> List[bool]:
        """Delete memories by ID.
        
        Args:
            ids: Memory IDs to delete
            
        Returns:
            List of success flags
        """
        results = []
        
        for memory_id in ids:
            success = await self.store.delete(memory_id)
            results.append(success)
        
        return results


# Create memory tools

def create_memory_tools(memory_manager: Optional[MemoryManager] = None) -> List[Tool]:
    """Create standard memory tools for agents.
    
    Args:
        memory_manager: Optional shared memory manager
        
    Returns:
        List of memory tools
    """
    if not memory_manager:
        memory_manager = MemoryManager()
    
    tools = []
    
    # Recall memories tool
    @create_tool(
        name="recall_memories",
        description="Recall memories relevant to one or more queries. Can run multiple queries in parallel."
    )
    async def recall_memories_tool(
        queries: List[str],
        limit: int = 10,
        context: ToolContext = None
    ) -> str:
        """Recall relevant memories."""
        memories = await memory_manager.recall(queries, limit)
        
        if not memories:
            return "No relevant memories found."
        
        # Format memories
        formatted = []
        for mem in memories:
            formatted.append(f"- {mem.get('content', 'Unknown')}")
        
        return f"Found {len(memories)} relevant memories:\n" + "\n".join(formatted)
    
    tools.append(recall_memories_tool)
    
    # Create memories tool
    @create_tool(
        name="create_memories",
        description="Save one or more new pieces of information to memory."
    )
    async def create_memories_tool(
        statements: List[str],
        context: ToolContext = None
    ) -> str:
        """Create new memories."""
        ids = await memory_manager.create(statements)
        return f"Created {len(ids)} new memories."
    
    tools.append(create_memories_tool)
    
    # Update memories tool
    @create_tool(
        name="update_memories",
        description="Update existing memories with corrected information."
    )
    async def update_memories_tool(
        updates: List[Dict[str, str]],
        context: ToolContext = None
    ) -> str:
        """Update memories."""
        results = await memory_manager.update(updates)
        success_count = sum(results)
        return f"Updated {success_count} of {len(updates)} memories."
    
    tools.append(update_memories_tool)
    
    # Delete memories tool
    @create_tool(
        name="delete_memories",
        description="Delete memories that are no longer relevant or incorrect."
    )
    async def delete_memories_tool(
        ids: List[str],
        context: ToolContext = None
    ) -> str:
        """Delete memories."""
        results = await memory_manager.delete(ids)
        success_count = sum(results)
        return f"Deleted {success_count} of {len(ids)} memories."
    
    tools.append(delete_memories_tool)
    
    # Consolidated manage memories tool
    @create_tool(
        name="manage_memories",
        description="Create, update, and/or delete memories in a single atomic operation. This is the preferred way to modify memories."
    )
    async def manage_memories_tool(
        creations: Optional[List[str]] = None,
        updates: Optional[List[Dict[str, str]]] = None,
        deletions: Optional[List[str]] = None,
        context: ToolContext = None
    ) -> str:
        """Manage memories atomically."""
        results = []
        
        if creations:
            ids = await memory_manager.create(creations)
            results.append(f"Created {len(ids)} memories")
        
        if updates:
            update_results = await memory_manager.update(updates)
            success_count = sum(update_results)
            results.append(f"Updated {success_count} memories")
        
        if deletions:
            delete_results = await memory_manager.delete(deletions)
            success_count = sum(delete_results)
            results.append(f"Deleted {success_count} memories")
        
        return "Memory operations completed: " + ", ".join(results)
    
    tools.append(manage_memories_tool)
    
    return tools