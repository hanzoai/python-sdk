"""Agent implementation for Hanzo Network."""

from typing import Any, Dict, List, Optional, Callable, Union
from dataclasses import dataclass, field
from enum import Enum

from .tool import Tool
from .state import NetworkState, Message


class ModelProvider(Enum):
    """Supported model providers."""
    OPENAI = "openai"
    ANTHROPIC = "anthropic"
    GOOGLE = "google"
    LOCAL = "local"
    CLI = "cli"


@dataclass
class ModelConfig:
    """Configuration for an AI model."""
    provider: ModelProvider
    model: str
    api_key: Optional[str] = None
    base_url: Optional[str] = None
    temperature: float = 0.7
    max_tokens: Optional[int] = None
    
    @classmethod
    def from_string(cls, model_str: str) -> "ModelConfig":
        """Create config from model string like 'anthropic/claude-3-5-sonnet'."""
        if "/" in model_str:
            provider_str, model = model_str.split("/", 1)
            provider = ModelProvider(provider_str)
        else:
            # Guess provider from model name
            if "gpt" in model_str:
                provider = ModelProvider.OPENAI
            elif "claude" in model_str:
                provider = ModelProvider.ANTHROPIC
            elif "gemini" in model_str:
                provider = ModelProvider.GOOGLE
            else:
                provider = ModelProvider.LOCAL
            model = model_str
        
        return cls(provider=provider, model=model)


@dataclass
class AgentLifecycle:
    """Lifecycle hooks for an agent."""
    on_start: Optional[Callable] = None
    on_finish: Optional[Callable] = None
    on_error: Optional[Callable] = None
    on_tool_call: Optional[Callable] = None


@dataclass
class Agent:
    """An AI agent that can use tools and participate in networks.
    
    Agents are the core building blocks of Hanzo Network. Each agent has:
    - A name and description
    - An optional model configuration
    - Tools it can use
    - Lifecycle hooks for customization
    - A system prompt
    """
    name: str
    description: str
    model: Optional[ModelConfig] = None
    tools: List[Tool] = field(default_factory=list)
    system: Optional[str] = None
    lifecycle: Optional[AgentLifecycle] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    async def run(
        self,
        prompt: Union[str, List[Message]],
        state: Optional[NetworkState] = None,
        context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Run the agent with a prompt.
        
        Args:
            prompt: User prompt or list of messages
            state: Network state (if running in a network)
            context: Additional context
            
        Returns:
            Agent result including output and tool calls
        """
        # Convert prompt to messages if string
        if isinstance(prompt, str):
            messages = [Message(role="user", content=prompt)]
        else:
            messages = prompt
        
        # Add system message if configured
        if self.system:
            messages = [Message(role="system", content=self.system)] + messages
        
        # Call lifecycle hook
        if self.lifecycle and self.lifecycle.on_start:
            result = await self.lifecycle.on_start(
                agent=self,
                messages=messages,
                state=state,
                context=context
            )
            if result and result.get("stop"):
                return result
            messages = result.get("messages", messages)
        
        try:
            # Execute with appropriate backend
            if self.model and isinstance(self.model, ModelConfig) and self.model.provider == ModelProvider.CLI:
                result = await self._execute_cli(messages, state, context)
            else:
                result = await self._execute_llm(messages, state, context)
            
            # Call finish hook
            if self.lifecycle and self.lifecycle.on_finish:
                await self.lifecycle.on_finish(
                    agent=self,
                    result=result,
                    state=state,
                    context=context
                )
            
            return result
            
        except Exception as e:
            # Call error hook
            if self.lifecycle and self.lifecycle.on_error:
                await self.lifecycle.on_error(
                    agent=self,
                    error=e,
                    state=state,
                    context=context
                )
            raise
    
    async def _execute_llm(
        self,
        messages: List[Message],
        state: Optional[NetworkState],
        context: Optional[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Execute using LLM backend."""
        # Convert tools to appropriate format
        tools = []
        if self.tools and self.model:
            if self.model.provider == ModelProvider.OPENAI:
                tools = [t.to_openai_function() for t in self.tools]
            elif self.model.provider == ModelProvider.ANTHROPIC:
                tools = [t.to_anthropic_tool() for t in self.tools]
            elif self.model.provider == ModelProvider.LOCAL:
                # Simple tool format for local LLMs
                tools = [{"name": t.name, "description": t.description} for t in self.tools]
        
        # Handle local LLM providers using hanzo/net
        if self.model and self.model.provider == ModelProvider.LOCAL:
            from ..llm import HanzoNetProvider
            
            # Determine engine type based on model config
            engine_type = "dummy"  # Default for testing
            if "mlx" in self.model.model.lower():
                engine_type = "mlx"
            elif "tinygrad" in self.model.model.lower():
                engine_type = "tinygrad"
            
            # Create hanzo/net provider
            provider = HanzoNetProvider(
                engine_type=engine_type,
                base_url=self.model.base_url
            )
            
            # Generate using distributed inference
            return await provider.generate(
                messages=messages,
                model=self.model.model,
                temperature=self.model.temperature,
                max_tokens=self.model.max_tokens,
                tools=tools
            )
        
        # For other providers or if local not available, return mock
        return {
            "output": [{"type": "text", "content": f"Mock response from {self.name}"}],
            "tool_calls": [],
            "usage": {"input_tokens": 100, "output_tokens": 50}
        }
    
    async def _execute_cli(
        self,
        messages: List[Message],
        state: Optional[NetworkState],
        context: Optional[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Execute using CLI tool."""
        # This would integrate with CLI tools from MCP
        # For now, return a mock result
        return {
            "output": [{"type": "text", "content": f"CLI response from {self.name}"}],
            "tool_calls": [],
            "usage": {}
        }
    
    def add_tool(self, tool: Tool) -> None:
        """Add a tool to this agent."""
        self.tools.append(tool)
    
    def remove_tool(self, tool_name: str) -> None:
        """Remove a tool by name."""
        self.tools = [t for t in self.tools if t.name != tool_name]


def create_agent(
    name: str,
    description: str,
    model: Optional[Union[str, ModelConfig]] = None,
    tools: Optional[List[Tool]] = None,
    system: Optional[str] = None,
    lifecycle: Optional[Dict[str, Callable]] = None,
    **metadata
) -> Agent:
    """Create an agent with the given configuration.
    
    Args:
        name: Agent name
        description: Agent description
        model: Model configuration (string or ModelConfig)
        tools: List of tools the agent can use
        system: System prompt
        lifecycle: Lifecycle hooks as dict
        **metadata: Additional metadata
        
    Returns:
        Configured Agent instance
    """
    # Convert model string to config if needed
    if isinstance(model, str):
        model = ModelConfig.from_string(model)
    
    # Convert lifecycle dict to object
    if lifecycle:
        lifecycle_obj = AgentLifecycle(
            on_start=lifecycle.get("on_start"),
            on_finish=lifecycle.get("on_finish"),
            on_error=lifecycle.get("on_error"),
            on_tool_call=lifecycle.get("on_tool_call")
        )
    else:
        lifecycle_obj = None
    
    return Agent(
        name=name,
        description=description,
        model=model,
        tools=tools or [],
        system=system,
        lifecycle=lifecycle_obj,
        metadata=metadata
    )