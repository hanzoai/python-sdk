"""UI streaming support for real-time updates."""

from __future__ import annotations

import asyncio
import time
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, AsyncIterator, Dict, List, Optional

from ..logger import logger


class UpdateType(Enum):
    """Type of UI update."""
    
    WORKFLOW_START = "workflow_start"
    """Workflow execution started."""
    
    WORKFLOW_COMPLETE = "workflow_complete"
    """Workflow execution completed."""
    
    STEP_START = "step_start"
    """Step execution started."""
    
    STEP_COMPLETE = "step_complete"
    """Step execution completed."""
    
    STEP_PROGRESS = "step_progress"
    """Step progress update."""
    
    AGENT_MESSAGE = "agent_message"
    """Message from an agent."""
    
    TOOL_CALL = "tool_call"
    """Tool was called."""
    
    ERROR = "error"
    """An error occurred."""
    
    LOG = "log"
    """Log message."""
    
    CUSTOM = "custom"
    """Custom update type."""


@dataclass
class StreamUpdate:
    """A single stream update."""
    
    execution_id: str
    """ID of the execution this update belongs to."""
    
    type: UpdateType
    """Type of update."""
    
    data: Dict[str, Any]
    """Update data."""
    
    timestamp: float = field(default_factory=time.time)
    """When the update was created."""
    
    metadata: Dict[str, Any] = field(default_factory=dict)
    """Additional metadata."""


class UIStreamer:
    """Manages UI streaming for workflow execution."""
    
    def __init__(self, buffer_size: int = 1000):
        """Initialize UI streamer.
        
        Args:
            buffer_size: Maximum updates to buffer
        """
        self.buffer_size = buffer_size
        self._queues: Dict[str, asyncio.Queue[StreamUpdate]] = {}
        self._subscribers: Dict[str, List[asyncio.Queue[StreamUpdate]]] = {}
        self._buffer: List[StreamUpdate] = []
        self._lock = asyncio.Lock()
        
    async def send(self, update: StreamUpdate) -> None:
        """Send an update to subscribers.
        
        Args:
            update: Update to send
        """
        async with self._lock:
            # Add to buffer
            self._buffer.append(update)
            if len(self._buffer) > self.buffer_size:
                self._buffer.pop(0)
                
            # Send to execution-specific subscribers
            if update.execution_id in self._subscribers:
                for queue in self._subscribers[update.execution_id]:
                    try:
                        await queue.put(update)
                    except asyncio.QueueFull:
                        logger.warning(f"UI stream queue full for execution {update.execution_id}")
                        
            # Send to global subscribers
            if "*" in self._subscribers:
                for queue in self._subscribers["*"]:
                    try:
                        await queue.put(update)
                    except asyncio.QueueFull:
                        logger.warning("UI stream queue full for global subscriber")
                        
    async def stream(
        self,
        execution_id: str | None = None,
        include_history: bool = True,
        queue_size: int = 100,
    ) -> AsyncIterator[StreamUpdate]:
        """Stream updates for an execution.
        
        Args:
            execution_id: Execution to stream, or None for all
            include_history: Whether to include buffered updates
            queue_size: Size of subscriber queue
            
        Yields:
            Stream updates
        """
        # Create subscriber queue
        queue: asyncio.Queue[StreamUpdate] = asyncio.Queue(maxsize=queue_size)
        
        # Subscribe
        sub_key = execution_id or "*"
        async with self._lock:
            if sub_key not in self._subscribers:
                self._subscribers[sub_key] = []
            self._subscribers[sub_key].append(queue)
            
            # Send history if requested
            if include_history:
                for update in self._buffer:
                    if execution_id is None or update.execution_id == execution_id:
                        await queue.put(update)
                        
        try:
            # Stream updates
            while True:
                update = await queue.get()
                yield update
                
        finally:
            # Unsubscribe
            async with self._lock:
                if sub_key in self._subscribers:
                    self._subscribers[sub_key].remove(queue)
                    if not self._subscribers[sub_key]:
                        del self._subscribers[sub_key]
                        
    async def send_workflow_start(
        self,
        execution_id: str,
        workflow_name: str,
        total_steps: int,
        **kwargs,
    ) -> None:
        """Send workflow start update."""
        await self.send(StreamUpdate(
            execution_id=execution_id,
            type=UpdateType.WORKFLOW_START,
            data={
                "workflow_name": workflow_name,
                "total_steps": total_steps,
                **kwargs,
            },
        ))
        
    async def send_workflow_complete(
        self,
        execution_id: str,
        success: bool,
        duration: float,
        **kwargs,
    ) -> None:
        """Send workflow completion update."""
        await self.send(StreamUpdate(
            execution_id=execution_id,
            type=UpdateType.WORKFLOW_COMPLETE,
            data={
                "success": success,
                "duration": duration,
                **kwargs,
            },
        ))
        
    async def send_step_start(
        self,
        execution_id: str,
        step_id: str,
        step_name: str,
        **kwargs,
    ) -> None:
        """Send step start update."""
        await self.send(StreamUpdate(
            execution_id=execution_id,
            type=UpdateType.STEP_START,
            data={
                "step_id": step_id,
                "step_name": step_name,
                **kwargs,
            },
        ))
        
    async def send_step_complete(
        self,
        execution_id: str,
        step_id: str,
        success: bool,
        duration: float,
        **kwargs,
    ) -> None:
        """Send step completion update."""
        await self.send(StreamUpdate(
            execution_id=execution_id,
            type=UpdateType.STEP_COMPLETE,
            data={
                "step_id": step_id,
                "success": success,
                "duration": duration,
                **kwargs,
            },
        ))
        
    async def send_step_progress(
        self,
        execution_id: str,
        step_id: str,
        progress: float,
        message: str | None = None,
        **kwargs,
    ) -> None:
        """Send step progress update.
        
        Args:
            execution_id: Execution ID
            step_id: Step ID
            progress: Progress percentage (0-100)
            message: Optional progress message
            **kwargs: Additional data
        """
        await self.send(StreamUpdate(
            execution_id=execution_id,
            type=UpdateType.STEP_PROGRESS,
            data={
                "step_id": step_id,
                "progress": progress,
                "message": message,
                **kwargs,
            },
        ))
        
    async def send_agent_message(
        self,
        execution_id: str,
        agent_name: str,
        role: str,
        content: str,
        **kwargs,
    ) -> None:
        """Send agent message update."""
        await self.send(StreamUpdate(
            execution_id=execution_id,
            type=UpdateType.AGENT_MESSAGE,
            data={
                "agent_name": agent_name,
                "role": role,
                "content": content,
                **kwargs,
            },
        ))
        
    async def send_tool_call(
        self,
        execution_id: str,
        tool_name: str,
        arguments: Dict[str, Any],
        result: Any | None = None,
        **kwargs,
    ) -> None:
        """Send tool call update."""
        await self.send(StreamUpdate(
            execution_id=execution_id,
            type=UpdateType.TOOL_CALL,
            data={
                "tool_name": tool_name,
                "arguments": arguments,
                "result": result,
                **kwargs,
            },
        ))
        
    async def send_error(
        self,
        execution_id: str,
        error: str,
        step_id: str | None = None,
        **kwargs,
    ) -> None:
        """Send error update."""
        await self.send(StreamUpdate(
            execution_id=execution_id,
            type=UpdateType.ERROR,
            data={
                "error": error,
                "step_id": step_id,
                **kwargs,
            },
        ))
        
    async def send_log(
        self,
        execution_id: str,
        level: str,
        message: str,
        **kwargs,
    ) -> None:
        """Send log message update."""
        await self.send(StreamUpdate(
            execution_id=execution_id,
            type=UpdateType.LOG,
            data={
                "level": level,
                "message": message,
                **kwargs,
            },
        ))
        
    def get_buffer(self, execution_id: str | None = None) -> List[StreamUpdate]:
        """Get buffered updates.
        
        Args:
            execution_id: Filter by execution ID
            
        Returns:
            List of buffered updates
        """
        if execution_id:
            return [u for u in self._buffer if u.execution_id == execution_id]
        return self._buffer.copy()
        
    def clear_buffer(self, execution_id: str | None = None) -> None:
        """Clear buffered updates.
        
        Args:
            execution_id: Clear only for specific execution
        """
        if execution_id:
            self._buffer = [u for u in self._buffer if u.execution_id != execution_id]
        else:
            self._buffer.clear()