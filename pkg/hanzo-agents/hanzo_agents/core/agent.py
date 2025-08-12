"""Agent base class and implementation."""

import json
from abc import ABC, abstractmethod
from typing import Any, Dict, List, Type, Generic, TypeVar, Optional
from datetime import datetime
from dataclasses import field, dataclass

from hanzo_agents.core.tool import Tool
from hanzo_agents.core.state import State

S = TypeVar("S", bound=State)


@dataclass
class ToolCall:
    """Represents a tool invocation."""

    tool: str
    arguments: Dict[str, Any]
    id: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return {"tool": self.tool, "arguments": self.arguments, "id": self.id}


@dataclass
class InferenceResult:
    """Result from agent inference."""

    agent: str
    content: Optional[str] = None
    tool_calls: List[ToolCall] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)
    timestamp: str = field(default_factory=lambda: datetime.utcnow().isoformat())

    def to_dict(self) -> Dict[str, Any]:
        return {
            "agent": self.agent,
            "content": self.content,
            "tool_calls": [tc.to_dict() for tc in self.tool_calls],
            "metadata": self.metadata,
            "timestamp": self.timestamp,
        }


class Agent(ABC, Generic[S]):
    """Base class for all agents.

    Agents encapsulate:
    - A specific skill or domain
    - Set of tools they can use
    - Model configuration
    - Prompting strategy

    Agents MUST NOT have side effects outside of tool calls.
    """

    name: str
    description: str
    tools: List[Tool[S]] = []
    model: Optional[str] = None  # e.g. "model://anthropic/claude-3-haiku"

    def __init__(self, **kwargs):
        """Initialize agent with optional overrides."""
        for k, v in kwargs.items():
            if hasattr(self, k):
                setattr(self, k, v)

    @abstractmethod
    async def run(
        self, state: S, history: "History", network: "Network[S]"
    ) -> InferenceResult:
        """Execute agent inference.

        Args:
            state: Current network state
            history: Conversation history
            network: Network instance for context

        Returns:
            InferenceResult with content and/or tool calls
        """
        pass

    def get_tools(self) -> List[Tool[S]]:
        """Get available tools for this agent."""
        return self.tools

    def get_tool_schemas(self) -> List[Dict[str, Any]]:
        """Get JSON schemas for all tools."""
        return [tool.get_schema() for tool in self.tools]

    async def execute_tool(
        self, tool_name: str, arguments: Dict[str, Any], network: "Network[S]"
    ) -> Any:
        """Execute a tool by name."""
        for tool in self.tools:
            if tool.name == tool_name:
                return await tool(network, **arguments)
        raise ValueError(f"Unknown tool: {tool_name}")

    def format_system_prompt(self) -> str:
        """Format system prompt with agent info and tools."""
        prompt = f"""You are {self.name}: {self.description}

You have access to the following tools:
"""
        for tool in self.tools:
            schema = tool.get_schema()
            prompt += f"\n- {tool.name}: {tool.description}"
            if schema.get("parameters", {}).get("properties"):
                prompt += f"\n  Parameters: {json.dumps(schema['parameters']['properties'], indent=2)}"

        prompt += "\n\nRespond with your analysis and any tool calls needed."
        return prompt


class AgentRegistry:
    """Registry for agent types."""

    _agents: Dict[str, Type[Agent]] = {}

    @classmethod
    def register(cls, agent_class: Type[Agent], name: Optional[str] = None):
        """Register an agent class."""
        name = name or agent_class.name
        cls._agents[name] = agent_class

    @classmethod
    def get(cls, name: str) -> Optional[Type[Agent]]:
        """Get agent class by name."""
        return cls._agents.get(name)

    @classmethod
    def list_agents(cls) -> List[str]:
        """List all registered agents."""
        return list(cls._agents.keys())

    @classmethod
    def create(cls, name: str, **kwargs) -> Agent:
        """Create agent instance."""
        agent_class = cls.get(name)
        if not agent_class:
            raise ValueError(f"Unknown agent: {name}")
        return agent_class(**kwargs)


# Example base agents


class PlanningAgent(Agent[S]):
    """Agent specialized in creating plans."""

    name = "planner"
    description = "Creates and refines plans"
    model = "model://anthropic/claude-3-haiku"

    async def run(
        self, state: S, history: "History", network: "Network[S]"
    ) -> InferenceResult:
        """Create or update plan based on state."""
        # This would call the actual model
        # For now, return a mock result
        return InferenceResult(
            agent=self.name,
            content="I need to analyze the requirements and create a plan.",
            tool_calls=[
                ToolCall(
                    tool="think",
                    arguments={"thought": "Breaking down the problem into steps..."},
                )
            ],
        )


class ReviewAgent(Agent[S]):
    """Agent specialized in reviewing work."""

    name = "reviewer"
    description = "Reviews and validates work"
    model = "model://openai/gpt-4"

    async def run(
        self, state: S, history: "History", network: "Network[S]"
    ) -> InferenceResult:
        """Review current state and provide feedback."""
        return InferenceResult(
            agent=self.name,
            content="Reviewing the current progress and checking for issues.",
            tool_calls=[],
        )


# Persona wrapper for quick agent creation


def create_agent(
    name: str,
    description: str,
    tools: List[Tool] = None,
    model: str = None,
    system_prompt: str = None,
) -> Type[Agent]:
    """Factory to create agent classes."""

    class CustomAgent(Agent):
        pass

    CustomAgent.name = name
    CustomAgent.description = description
    CustomAgent.tools = tools or []
    CustomAgent.model = model

    if system_prompt:
        CustomAgent._system_prompt = system_prompt

    # Register the agent
    AgentRegistry.register(CustomAgent, name)

    return CustomAgent
