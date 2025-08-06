"""Router system for agent networks in Hanzo Network."""

from typing import Any, Callable, Dict, Optional, Union, Protocol
from dataclasses import dataclass
from enum import Enum

from hanzo_network.core.agent import Agent, ModelConfig
from hanzo_network.core.state import NetworkState


class RouterDecision(Enum):
    """Possible router decisions."""
    CONTINUE = "continue"  # Continue to next agent
    STOP = "stop"  # Stop network execution
    
    
class RouterArgs:
    """Arguments provided to router functions."""
    
    def __init__(
        self,
        network: Any,  # Network instance
        state: NetworkState,
        stack: list[Agent],
        call_count: int,
        last_result: Optional[Dict[str, Any]] = None,
        last_agent: Optional[Agent] = None
    ):
        self.network = network
        self.state = state
        self.stack = stack
        self.call_count = call_count
        self.last_result = last_result
        self.last_agent = last_agent
        
    def get_last_output(self) -> Optional[str]:
        """Get the last text output from the previous agent."""
        if not self.last_result:
            return None
            
        output = self.last_result.get("output", [])
        for item in reversed(output):
            if item.get("type") == "text":
                return item.get("content")
        return None


class RouterFunction(Protocol):
    """Protocol for router functions."""
    def __call__(self, args: RouterArgs) -> Optional[Agent]:
        """Return next agent or None to stop."""
        ...


@dataclass
class Router:
    """Base router class."""
    name: str
    description: str
    handler: RouterFunction
    
    def __call__(self, args: RouterArgs) -> Optional[Agent]:
        """Call the router."""
        return self.handler(args)


@dataclass
class RoutingAgent(Agent):
    """Special agent for routing decisions.
    
    Routing agents are like regular agents but:
    - Cannot have tools
    - Have special lifecycle for routing
    """
    
    def __post_init__(self):
        """Ensure no tools on routing agents."""
        if self.tools:
            raise ValueError("Routing agents cannot have tools")
    
    async def route(
        self,
        args: RouterArgs
    ) -> Optional[Agent]:
        """Make a routing decision using LLM.
        
        Args:
            args: Router arguments
            
        Returns:
            Next agent or None to stop
        """
        # Build prompt for routing decision
        prompt = self._build_routing_prompt(args)
        
        # Run agent to get decision
        result = await self.run(prompt, state=args.state)
        
        # Parse decision from result
        return self._parse_routing_decision(result, args)
    
    def _build_routing_prompt(self, args: RouterArgs) -> str:
        """Build prompt for routing decision."""
        available_agents = args.network.agents
        
        prompt_parts = [
            "You are a routing agent. Your job is to decide which agent to call next or whether to stop.",
            "",
            f"Call count: {args.call_count}",
            f"Available agents: {', '.join([a.name for a in available_agents])}",
            ""
        ]
        
        if args.last_agent:
            prompt_parts.append(f"Last agent: {args.last_agent.name}")
            
        if args.last_result:
            output = args.get_last_output()
            if output:
                prompt_parts.append(f"Last output: {output[:200]}...")
        
        prompt_parts.extend([
            "",
            "Based on the current state, which agent should run next?",
            "Respond with the agent name or 'STOP' to end execution."
        ])
        
        return "\n".join(prompt_parts)
    
    def _parse_routing_decision(
        self,
        result: Dict[str, Any],
        args: RouterArgs
    ) -> Optional[Agent]:
        """Parse routing decision from agent result."""
        output = result.get("output", [])
        
        for item in output:
            if item.get("type") == "text":
                content = item.get("content", "").strip().upper()
                
                if content == "STOP":
                    return None
                
                # Find agent by name
                for agent in args.network.agents:
                    if agent.name.upper() == content:
                        return agent
        
        # Default to stop if can't parse
        return None


def create_router(
    handler: RouterFunction,
    name: str = "custom_router",
    description: str = "Custom router"
) -> Router:
    """Create a code-based router.
    
    Args:
        handler: Router function
        name: Router name
        description: Router description
        
    Returns:
        Router instance
    """
    return Router(
        name=name,
        description=description,
        handler=handler
    )


def create_routing_agent(
    name: str,
    description: str,
    model: Optional[Union[str, ModelConfig]] = None,
    system: Optional[str] = None,
    **kwargs
) -> RoutingAgent:
    """Create a routing agent for LLM-based routing.
    
    Args:
        name: Agent name
        description: Agent description
        model: Model configuration
        system: System prompt for routing
        **kwargs: Additional agent parameters
        
    Returns:
        RoutingAgent instance
    """
    # Default system prompt for routing
    if not system:
        system = """You are a routing agent responsible for orchestrating a network of AI agents.
Your job is to analyze the current state and decide which agent should run next.

Guidelines:
- Consider what has been accomplished so far
- Identify what still needs to be done
- Choose the most appropriate agent for the next step
- Return 'STOP' when the task is complete

Be efficient and avoid unnecessary agent calls."""
    
    return RoutingAgent(
        name=name,
        description=description,
        model=model,
        system=system,
        tools=[],  # No tools for routing agents
        **kwargs
    )


def get_default_routing_agent(
    model: Optional[Union[str, ModelConfig]] = None
) -> RoutingAgent:
    """Get the default routing agent.
    
    Args:
        model: Model to use (defaults to Claude Sonnet)
        
    Returns:
        Default RoutingAgent
    """
    if not model:
        from hanzo_network.core.agent import ModelConfig, ModelProvider
        # Use local dummy model for default router
        model = ModelConfig(
            provider=ModelProvider.LOCAL,
            model="llama3.2",
            temperature=0.3
        )
    
    return create_routing_agent(
        name="default_router",
        description="Default routing agent for network orchestration",
        model=model,
        system="""You are the default routing agent. Analyze the conversation and network state to decide:

1. If the user's request has been fully addressed -> return STOP
2. If more work is needed -> return the name of the most appropriate agent

Consider:
- What has each agent already done?
- What remains to be accomplished?
- Which agent is best suited for the next step?
- Are we going in circles? If so, return STOP

Be concise. Respond with just the agent name or STOP."""
    )


# Common routing patterns as functions

def sequential_router(agents: list[Agent]) -> RouterFunction:
    """Create a router that calls agents in sequence.
    
    Args:
        agents: List of agents to call in order
        
    Returns:
        Router function
    """
    def handler(args: RouterArgs) -> Optional[Agent]:
        if args.call_count < len(agents):
            return agents[args.call_count]
        return None
    
    return handler


def conditional_router(
    conditions: list[tuple[Callable[[RouterArgs], bool], Agent]]
) -> RouterFunction:
    """Create a router based on conditions.
    
    Args:
        conditions: List of (condition_fn, agent) tuples
        
    Returns:
        Router function
    """
    def handler(args: RouterArgs) -> Optional[Agent]:
        for condition_fn, agent in conditions:
            if condition_fn(args):
                return agent
        return None
    
    return handler


def state_based_router(
    state_key: str,
    state_map: Dict[Any, Agent]
) -> RouterFunction:
    """Create a router based on state values.
    
    Args:
        state_key: Key to check in state.data
        state_map: Map of state values to agents
        
    Returns:
        Router function
    """
    def handler(args: RouterArgs) -> Optional[Agent]:
        value = args.state.data.get(state_key)
        return state_map.get(value)
    
    return handler