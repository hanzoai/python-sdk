"""Tool system for agents in Hanzo Network."""

from typing import Any, Callable, Dict, Optional, Protocol, TypedDict
from dataclasses import dataclass
import inspect
from pydantic import BaseModel, create_model


class ToolContext(TypedDict):
    """Context provided to tool handlers."""
    network: Optional[Any]  # Network instance
    state: Optional[Any]  # Network state
    agent: Optional[Any]  # Current agent


class ToolHandler(Protocol):
    """Protocol for tool handler functions."""
    async def __call__(
        self,
        parameters: Dict[str, Any],
        context: ToolContext
    ) -> Any:
        ...


@dataclass
class Tool:
    """A tool that agents can use.
    
    Tools are functions that agents can call to perform actions or retrieve information.
    """
    name: str
    description: str
    parameters: type[BaseModel]
    handler: ToolHandler
    
    async def call(
        self,
        parameters: Dict[str, Any],
        context: Optional[ToolContext] = None
    ) -> Any:
        """Call the tool with given parameters.
        
        Args:
            parameters: Tool parameters
            context: Execution context
            
        Returns:
            Tool result
        """
        # Validate parameters
        validated_params = self.parameters(**parameters)
        
        # Call handler
        ctx = context or {}
        return await self.handler(validated_params.dict(), ctx)
    
    def to_openai_function(self) -> Dict[str, Any]:
        """Convert to OpenAI function format."""
        schema = self.parameters.schema()
        
        return {
            "name": self.name,
            "description": self.description,
            "parameters": {
                "type": "object",
                "properties": schema.get("properties", {}),
                "required": schema.get("required", [])
            }
        }
    
    def to_anthropic_tool(self) -> Dict[str, Any]:
        """Convert to Anthropic tool format."""
        schema = self.parameters.schema()
        
        return {
            "name": self.name,
            "description": self.description,
            "input_schema": {
                "type": "object",
                "properties": schema.get("properties", {}),
                "required": schema.get("required", [])
            }
        }


def create_tool(
    name: str,
    description: str,
    parameters: Optional[type[BaseModel]] = None,
    handler: Optional[ToolHandler] = None
) -> Callable:
    """Create a tool using decorator syntax or direct call.
    
    Usage:
        # As decorator
        @create_tool(
            name="search",
            description="Search the web",
            parameters=SearchParams
        )
        async def search_handler(params, context):
            return f"Searching for {params['query']}"
        
        # Direct call
        tool = create_tool(
            name="search",
            description="Search the web",
            parameters=SearchParams,
            handler=search_handler
        )
    
    Args:
        name: Tool name
        description: Tool description
        parameters: Pydantic model for parameters
        handler: Tool handler function
        
    Returns:
        Tool instance or decorator
    """
    def decorator(func: ToolHandler) -> Tool:
        # Extract parameters from function signature if not provided
        nonlocal parameters
        if parameters is None:
            sig = inspect.signature(func)
            param_fields = {}
            
            for param_name, param in sig.parameters.items():
                if param_name in ['self', 'context', 'ctx']:
                    continue
                
                # Get type annotation
                param_type = param.annotation if param.annotation != inspect.Parameter.empty else Any
                default = param.default if param.default != inspect.Parameter.empty else ...
                
                param_fields[param_name] = (param_type, default)
            
            # Create dynamic Pydantic model
            if param_fields:
                parameters = create_model(f"{name}_params", **param_fields)
            else:
                parameters = create_model(f"{name}_params")
        
        return Tool(
            name=name,
            description=description,
            parameters=parameters,
            handler=func
        )
    
    if handler is not None:
        # Direct call with handler
        return decorator(handler)
    else:
        # Return decorator
        return decorator