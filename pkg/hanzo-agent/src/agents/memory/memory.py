"""Core memory system for agents."""

from __future__ import annotations

import time
from typing import Any, Callable, Dict, List, Optional

from ..agent import Agent
from ..items import TResponseInputItem, ItemHelpers
from ..logger import logger
from ..run_context import RunContextWrapper, TContext
from .types import MemoryEntry, MemoryType
from .store import MemoryStore, InMemoryMemoryStore
from .retriever import MemoryRetriever, SemanticRetriever




class Memory:
    """Memory system for agents."""
    
    def __init__(
        self,
        store: MemoryStore | None = None,
        retriever: MemoryRetriever | None = None,
        max_entries: int = 1000,
        auto_compress: bool = True,
        compress_threshold: int = 100,
    ):
        """Initialize memory system.
        
        Args:
            store: Memory storage backend
            retriever: Memory retrieval strategy
            max_entries: Maximum number of entries to keep
            auto_compress: Whether to automatically compress old memories
            compress_threshold: Number of entries before compression
        """
        self.store = store or InMemoryMemoryStore()
        self.retriever = retriever or SemanticRetriever()
        self.max_entries = max_entries
        self.auto_compress = auto_compress
        self.compress_threshold = compress_threshold
        
    # Backwards-compatible aliases for tests and existing code
    async def add(
        self,
        content: str,
        type: MemoryType = MemoryType.CONVERSATION,
        agent_name: str | None = None,
        importance: float = 1.0,
        metadata: Dict[str, Any] | None = None,
    ) -> MemoryEntry:
        return await self.remember(
            content=content,
            type=type,
            agent_name=agent_name,
            importance=importance,
            metadata=metadata,
        )

    async def search(
        self,
        query: str | None = None,
        limit: int = 10,
        type: MemoryType | None = None,
        agent_name: str | None = None,
        min_importance: float = 0.0,
    ) -> List[MemoryEntry]:
        return await self.recall(
            query=query,
            type=type,
            agent_name=agent_name,
            limit=limit,
            min_importance=min_importance,
        )

    async def get_all(self) -> List[MemoryEntry]:
        return await self.store.list()
        
    async def remember(
        self,
        content: str,
        type: MemoryType = MemoryType.CONVERSATION,
        agent_name: str | None = None,
        importance: float = 1.0,
        metadata: Dict[str, Any] | None = None,
    ) -> MemoryEntry:
        """Store a new memory.
        
        Args:
            content: The content to remember
            type: Type of memory
            agent_name: Name of the agent creating the memory
            importance: Importance score
            metadata: Additional metadata
            
        Returns:
            The created memory entry
        """
        # Check if we need to compress
        if self.auto_compress:
            count = await self.store.count()
            if count >= self.compress_threshold:
                await self._compress_memories()
                
        # Create memory entry
        entry = await self.store.add(
            content=content,
            type=type,
            agent_name=agent_name,
            importance=importance,
            metadata=metadata or {},
        )
        
        # Ensure we don't exceed the max_entries after adding
        if self.auto_compress:
            count_after = await self.store.count()
            if count_after > self.max_entries:
                await self._compress_memories()
        
        logger.debug(f"Stored memory: {entry.id} ({type.value})")
        
        return entry
        
    async def recall(
        self,
        query: str | None = None,
        type: MemoryType | None = None,
        agent_name: str | None = None,
        limit: int = 10,
        min_importance: float = 0.0,
    ) -> List[MemoryEntry]:
        """Retrieve memories.
        
        Args:
            query: Query for semantic search
            type: Filter by memory type
            agent_name: Filter by agent name
            limit: Maximum number of results
            min_importance: Minimum importance threshold
            
        Returns:
            List of matching memories
        """
        # Get all memories matching filters
        memories = await self.store.list(
            type=type,
            agent_name=agent_name,
            min_importance=min_importance,
        )
        
        # Use retriever to find best matches
        if query and self.retriever:
            memories = await self.retriever.retrieve(
                query=query,
                memories=memories,
                limit=limit,
            )
        else:
            # Just return most recent
            memories = sorted(memories, key=lambda m: m.timestamp, reverse=True)[:limit]
            
        # Update access counts
        for memory in memories:
            memory.access_count += 1
            memory.last_accessed = time.time()
            await self.store.update(memory)
            
        return memories
        
    async def forget(self, memory_id: str) -> None:
        """Remove a specific memory."""
        await self.store.delete(memory_id)
        logger.debug(f"Deleted memory: {memory_id}")
        
    async def clear(
        self,
        type: MemoryType | None = None,
        agent_name: str | None = None,
    ) -> int:
        """Clear memories.
        
        Args:
            type: Clear only memories of this type
            agent_name: Clear only memories from this agent
            
        Returns:
            Number of memories cleared
        """
        memories = await self.store.list(type=type, agent_name=agent_name)
        
        for memory in memories:
            await self.store.delete(memory.id)
            
        logger.debug(f"Cleared {len(memories)} memories")
        return len(memories)
        
    async def reflect(
        self,
        agent: Agent[TContext],
        context: RunContextWrapper[TContext] | None = None,
        recent_limit: int = 20,
    ) -> MemoryEntry:
        """Generate a reflection based on recent memories.
        
        This allows the agent to synthesize and learn from recent experiences.
        
        Args:
            agent: The agent doing the reflection
            context: Optional context
            recent_limit: Number of recent memories to consider
            
        Returns:
            The reflection memory entry
        """
        # Get recent memories
        recent = await self.recall(
            agent_name=agent.name,
            limit=recent_limit,
        )
        
        if not recent:
            content = "No recent memories to reflect on."
        else:
            # Build reflection prompt
            memory_text = "\n".join([
                f"- [{m.type.value}] {m.content}"
                for m in recent
            ])
            
            # Use agent to generate reflection
            from ..run import Runner
            
            reflection_agent = agent.clone(
                instructions=(
                    "You are reflecting on recent memories and experiences. "
                    "Synthesize key insights, patterns, and learnings."
                ),
            )
            
            result = await Runner.run(
                starting_agent=reflection_agent,
                input=f"Reflect on these recent memories:\n\n{memory_text}",
                context=context.context if context else None,
                max_turns=1,
            )
            
            content = ItemHelpers.text_message_outputs(result.new_items)
            
        # Store reflection
        reflection = await self.remember(
            content=content,
            type=MemoryType.REFLECTION,
            agent_name=agent.name,
            importance=0.8,
            metadata={"recent_memory_count": len(recent)},
        )
        
        return reflection
        
    async def _compress_memories(self) -> None:
        """Compress old memories to save space."""
        # Get all memories sorted by importance and recency
        memories = await self.store.list()
        
        # Score memories
        now = time.time()
        scored = []
        
        for memory in memories:
            # Calculate score based on importance, recency, and access
            recency_score = 1.0 / (1.0 + (now - memory.timestamp) / 86400)  # Days
            access_score = min(1.0, memory.access_count / 10)
            
            score = (
                memory.importance * 0.5 +
                recency_score * 0.3 +
                access_score * 0.2
            )
            
            scored.append((score, memory))
            
        # Sort by score
        scored.sort(key=lambda x: x[0], reverse=True)
        
        # Keep top memories
        to_keep = min(self.max_entries, len(scored))
        to_delete = len(scored) - to_keep
        
        if to_delete > 0:
            # Delete lowest scored memories
            for _, memory in scored[to_keep:]:
                await self.store.delete(memory.id)
                
            logger.debug(f"Compressed memories: deleted {to_delete} entries")
            
    def create_agent_wrapper(self, agent: Agent[TContext]) -> Agent[TContext]:
        """Create an agent wrapper with memory capabilities.
        
        This returns a new agent that automatically stores and retrieves memories.
        """
        memory = self
        
        async def memory_instructions(ctx: RunContextWrapper[TContext], agent: Agent[TContext]) -> str:
            # Get base instructions
            base = await agent.get_system_prompt(ctx)
            
            # Retrieve relevant memories
            if ctx and hasattr(ctx, "last_message"):
                memories = await memory.recall(
                    query=ctx.last_message,
                    agent_name=agent.name,
                    limit=5,
                )
                
                if memories:
                    memory_text = "\n".join([
                        f"- {m.content}"
                        for m in memories
                    ])
                    
                    return f"{base}\n\nRelevant memories:\n{memory_text}"
                    
            return base
            
        # Create memory-enabled agent
        return agent.clone(
            instructions=memory_instructions,
            hooks=MemoryAgentHooks(memory, agent.name),
        )


class MemoryAgentHooks:
    """Agent hooks for automatic memory management."""
    
    def __init__(self, memory: Memory, agent_name: str):
        self.memory = memory
        self.agent_name = agent_name
        
    async def on_start(self, context: RunContextWrapper[Any], agent: Agent[Any]) -> None:
        """Store conversation start."""
        await self.memory.remember(
            content="Conversation started",
            type=MemoryType.CONVERSATION,
            agent_name=self.agent_name,
            importance=0.3,
        )
        
    async def on_end(self, context: RunContextWrapper[Any], agent: Agent[Any]) -> None:
        """Store conversation end."""
        await self.memory.remember(
            content="Conversation ended",
            type=MemoryType.CONVERSATION,
            agent_name=self.agent_name,
            importance=0.3,
        )
