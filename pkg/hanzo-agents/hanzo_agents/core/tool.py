"""Tool system for agent side-effects."""

from typing import TypeVar, Generic, Dict, Any, Optional, Type, Callable
from abc import ABC, abstractmethod
from pydantic import BaseModel
import inspect
from functools import wraps
import asyncio
import json


S = TypeVar("S")  # State type


class Tool(ABC, Generic[S]):
    """Base class for agent tools.
    
    Tools are the ONLY way agents can perform side-effects.
    All tool operations must be:
    - Deterministic
    - Typed (via Parameters model)
    - State-mutating in an explicit way
    """
    
    name: str
    description: str
    parameters: Type[BaseModel] = BaseModel
    
    @abstractmethod
    def handle(self, **kwargs) -> Any:
        """Execute the tool operation.
        
        The network parameter is injected automatically and provides
        access to state and other network resources.
        """
        pass
    
    def get_schema(self) -> Dict[str, Any]:
        """Get JSON schema for tool parameters."""
        if hasattr(self.parameters, "model_json_schema"):
            schema = self.parameters.model_json_schema()
        else:
            schema = {"type": "object", "properties": {}}
        
        return {
            "name": self.name,
            "description": self.description,
            "parameters": schema
        }
    
    def validate_params(self, **kwargs) -> Dict[str, Any]:
        """Validate and parse parameters."""
        if self.parameters and self.parameters != BaseModel:
            # Use Pydantic for validation
            params = self.parameters(**kwargs)
            return params.model_dump()
        return kwargs
    
    async def __call__(self, network: "Network[S]", **kwargs) -> Any:
        """Execute tool with network context."""
        # Validate parameters
        validated = self.validate_params(**kwargs)
        
        # Inject network into handle method
        sig = inspect.signature(self.handle)
        if "network" in sig.parameters:
            validated["network"] = network
        
        # Execute
        if asyncio.iscoroutinefunction(self.handle):
            result = await self.handle(**validated)
        else:
            result = self.handle(**validated)
        
        return result


class ToolRegistry:
    """Global registry for available tools."""
    
    _tools: Dict[str, Type[Tool]] = {}
    _instances: Dict[str, Tool] = {}
    
    @classmethod
    def register(cls, tool_class: Type[Tool], name: Optional[str] = None):
        """Register a tool class."""
        name = name or tool_class.name
        cls._tools[name] = tool_class
    
    @classmethod
    def get(cls, name: str) -> Optional[Type[Tool]]:
        """Get tool class by name."""
        return cls._tools.get(name)
    
    @classmethod
    def list_tools(cls) -> list[str]:
        """List all registered tool names."""
        return list(cls._tools.keys())
    
    @classmethod
    def create_instance(cls, name: str, **kwargs) -> Tool:
        """Create tool instance."""
        if name not in cls._instances:
            tool_class = cls.get(name)
            if not tool_class:
                raise ValueError(f"Unknown tool: {name}")
            cls._instances[name] = tool_class(**kwargs)
        return cls._instances[name]
    
    @classmethod
    def clear(cls):
        """Clear all registrations (for testing)."""
        cls._tools.clear()
        cls._instances.clear()


def tool(name: str, description: str, parameters: Optional[Type[BaseModel]] = None):
    """Decorator to create tools from functions."""
    
    def decorator(func: Callable) -> Type[Tool]:
        # Extract parameter schema from function signature if not provided
        if parameters is None:
            sig = inspect.signature(func)
            fields = {}
            for param_name, param in sig.parameters.items():
                if param_name in ["self", "network"]:
                    continue
                # Simple type mapping
                param_type = param.annotation if param.annotation != inspect.Parameter.empty else Any
                fields[param_name] = (param_type, param.default if param.default != inspect.Parameter.empty else ...)
            
            # Create Pydantic model dynamically
            Parameters = type("Parameters", (BaseModel,), {"__annotations__": fields})
        else:
            Parameters = parameters
        
        # Create tool class
        class FunctionTool(Tool):
            def __init__(self):
                self.name = name
                self.description = description
                self.parameters = Parameters
            
            def handle(self, **kwargs):
                return func(**kwargs)
        
        # Register and return
        ToolRegistry.register(FunctionTool, name)
        return FunctionTool
    
    return decorator


# Built-in tools

class ThinkTool(Tool[S]):
    """Tool for agents to think/reason without side effects."""
    
    name = "think"
    description = "Think about the problem and plan next steps"
    
    class Parameters(BaseModel):
        thought: str
    
    def handle(self, thought: str, network: "Network[S]") -> str:
        """Record thought in history."""
        # No state mutation, just returns for history
        return f"Thought: {thought}"


class MemoryStoreTool(Tool[S]):
    """Store information in long-term memory."""
    
    name = "memory_store"
    description = "Store information for future reference"
    
    class Parameters(BaseModel):
        key: str
        value: Dict[str, Any]
        metadata: Optional[Dict[str, Any]] = None
    
    async def handle(self, key: str, value: Dict[str, Any], 
                     metadata: Optional[Dict[str, Any]], 
                     network: "Network[S]") -> str:
        """Store in memory."""
        if network.memory_kv:
            await network.memory_kv.save(key, {
                "value": value,
                "metadata": metadata or {}
            })
            return f"Stored '{key}' in memory"
        return "No memory backend available"


class MemoryRecallTool(Tool[S]):
    """Recall information from memory."""
    
    name = "memory_recall"
    description = "Recall stored information"
    
    class Parameters(BaseModel):
        key: str
    
    async def handle(self, key: str, network: "Network[S]") -> Any:
        """Recall from memory."""
        if network.memory_kv:
            data = await network.memory_kv.load(key)
            if data:
                return data.get("value", data)
        return None


class MemorySearchTool(Tool[S]):
    """Search vector memory."""
    
    name = "memory_search"
    description = "Search for relevant memories"
    
    class Parameters(BaseModel):
        query: str
        k: int = 5
    
    async def handle(self, query: str, k: int, network: "Network[S]") -> list[str]:
        """Search vector memory."""
        if network.memory_vector:
            return await network.memory_vector.query(query, k=k)
        return []


# Register built-in tools
ToolRegistry.register(ThinkTool)
ToolRegistry.register(MemoryStoreTool)
ToolRegistry.register(MemoryRecallTool)
ToolRegistry.register(MemorySearchTool)