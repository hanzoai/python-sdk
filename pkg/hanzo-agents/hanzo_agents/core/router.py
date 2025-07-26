"""Router system for agent orchestration."""

from typing import TypeVar, Callable, Optional, List, Type, Dict, Any
from abc import ABC, abstractmethod
from enum import Enum

from hanzo_agents.core.agent import Agent, InferenceResult
from hanzo_agents.core.state import State


S = TypeVar("S", bound=State)

# Router function type
RouterFn = Callable[
    ["Network[S]", int, Optional[InferenceResult], List[Type[Agent[S]]]],
    Optional[Type[Agent[S]]]
]


class RouterType(Enum):
    """Types of routers."""
    DETERMINISTIC = "deterministic"
    LLM_BASED = "llm_based"
    HYBRID = "hybrid"


class Router(ABC):
    """Base router class."""
    
    router_type: RouterType = RouterType.DETERMINISTIC
    
    @abstractmethod
    def route(self, 
              network: "Network[S]", 
              call_count: int,
              last_result: Optional[InferenceResult],
              agent_stack: List[Type[Agent[S]]]) -> Optional[Type[Agent[S]]]:
        """Determine next agent to run.
        
        Args:
            network: Current network instance
            call_count: Number of agents called so far
            last_result: Result from previous agent
            agent_stack: Available agents
            
        Returns:
            Next agent class or None to stop
        """
        pass


class DeterministicRouter(Router):
    """Code-based deterministic router."""
    
    router_type = RouterType.DETERMINISTIC
    
    def __init__(self, routing_fn: RouterFn[S]):
        """Initialize with routing function."""
        self.routing_fn = routing_fn
    
    def route(self, network, call_count, last_result, agent_stack):
        """Use provided function for routing."""
        return self.routing_fn(network, call_count, last_result, agent_stack)


class LLMRouter(Router):
    """LLM-based router for dynamic decisions."""
    
    router_type = RouterType.LLM_BASED
    
    def __init__(self, model: str = "model://anthropic/claude-3-haiku"):
        """Initialize with model."""
        self.model = model
    
    async def route_async(self, network, call_count, last_result, agent_stack):
        """Async routing with LLM call."""
        # Build context
        context = {
            "state": network.state.to_dict(),
            "call_count": call_count,
            "last_agent": last_result.agent if last_result else None,
            "available_agents": [
                {"name": agent.name, "description": agent.description}
                for agent in agent_stack
            ]
        }
        
        # Call LLM (mock for now)
        # In real implementation, this would use the model adapter
        prompt = f"""Given the current state and available agents, which agent should run next?

State: {context['state']}
Last agent: {context['last_agent']}
Available agents: {context['available_agents']}

Respond with just the agent name or 'none' to stop."""
        
        # Mock response
        next_agent_name = "none"  # Would come from LLM
        
        if next_agent_name == "none":
            return None
        
        # Find agent by name
        for agent in agent_stack:
            if agent.name == next_agent_name:
                return agent
        
        return None
    
    def route(self, network, call_count, last_result, agent_stack):
        """Sync wrapper for compatibility."""
        # In practice, this would be handled by the network's async context
        import asyncio
        return asyncio.create_task(
            self.route_async(network, call_count, last_result, agent_stack)
        )


class HybridRouter(Router):
    """Combines deterministic and LLM routing."""
    
    router_type = RouterType.HYBRID
    
    def __init__(self, 
                 deterministic_fn: Optional[RouterFn[S]] = None,
                 llm_model: str = "model://anthropic/claude-3-haiku",
                 llm_threshold: float = 0.7):
        """Initialize hybrid router.
        
        Args:
            deterministic_fn: Primary routing function
            llm_model: Model for fallback routing
            llm_threshold: Confidence threshold for LLM routing
        """
        self.deterministic_fn = deterministic_fn
        self.llm_router = LLMRouter(llm_model)
        self.llm_threshold = llm_threshold
    
    def route(self, network, call_count, last_result, agent_stack):
        """Try deterministic first, fall back to LLM."""
        # Try deterministic routing
        if self.deterministic_fn:
            next_agent = self.deterministic_fn(network, call_count, last_result, agent_stack)
            if next_agent is not None:
                return next_agent
        
        # Fall back to LLM
        return self.llm_router.route(network, call_count, last_result, agent_stack)


# Common routing patterns

def sequential_router(agent_sequence: List[Type[Agent[S]]]) -> RouterFn[S]:
    """Create router that runs agents in sequence."""
    def router(network, call_count, last_result, agent_stack):
        if call_count < len(agent_sequence):
            return agent_sequence[call_count]
        return None
    return router


def conditional_router(conditions: Dict[str, Type[Agent[S]]]) -> RouterFn[S]:
    """Create router based on state conditions.
    
    Args:
        conditions: Dict mapping condition names to agents
        
    Example:
        router = conditional_router({
            "needs_plan": PlanningAgent,
            "needs_review": ReviewAgent,
            "needs_test": TestingAgent
        })
    """
    def router(network, call_count, last_result, agent_stack):
        state_dict = network.state.to_dict()
        
        # Check each condition
        for condition, agent in conditions.items():
            if state_dict.get(condition, False):
                return agent
        
        return None
    return router


def round_robin_router(agents: List[Type[Agent[S]]], max_rounds: int = 10) -> RouterFn[S]:
    """Create router that cycles through agents."""
    def router(network, call_count, last_result, agent_stack):
        if call_count >= max_rounds * len(agents):
            return None
        return agents[call_count % len(agents)]
    return router


def state_based_router(state_field: str, 
                      transitions: Dict[Any, Type[Agent[S]]],
                      default: Optional[Type[Agent[S]]] = None) -> RouterFn[S]:
    """Create router based on state field value.
    
    Args:
        state_field: Name of state field to check
        transitions: Mapping of field values to agents
        default: Default agent if no match
    """
    def router(network, call_count, last_result, agent_stack):
        state_dict = network.state.to_dict()
        value = state_dict.get(state_field)
        
        if value in transitions:
            return transitions[value]
        
        return default
    return router