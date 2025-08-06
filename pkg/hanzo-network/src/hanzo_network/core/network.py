"""Network implementation for orchestrating multiple agents."""

from typing import Any, Dict, List, Optional, Union, TypeVar, Generic
from dataclasses import dataclass, field
from datetime import datetime

from hanzo_network.core.agent import Agent
from hanzo_network.core.router import (
    Router, RouterFunction, RouterArgs, RoutingAgent,
    get_default_routing_agent
)
from hanzo_network.core.state import NetworkState


T = TypeVar('T')


@dataclass
class NetworkConfig(Generic[T]):
    """Configuration for a network."""
    name: str
    agents: List[Agent]
    router: Optional[Union[Router, RouterFunction, RoutingAgent]] = None
    default_model: Optional[str] = None
    max_iterations: int = 10
    default_state: Optional[NetworkState[T]] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


class Network(Generic[T]):
    """A network of agents that work together.
    
    Networks combine multiple agents with:
    - Shared state between agents
    - A router that decides agent execution order
    - Execution loop that runs until completion
    """
    
    def __init__(self, config: NetworkConfig[T]):
        """Initialize network with configuration.
        
        Args:
            config: Network configuration
        """
        self.name = config.name
        self.agents = config.agents
        self.router = config.router
        self.default_model = config.default_model
        self.max_iterations = config.max_iterations
        self.metadata = config.metadata
        
        # Initialize state
        if config.default_state:
            self.state = config.default_state
        else:
            self.state = NetworkState[T]()
        
        # Create agent lookup
        self.agent_map = {agent.name: agent for agent in self.agents}
        
        # Setup default router if needed
        if not self.router:
            self.router = get_default_routing_agent(model=self.default_model)
    
    async def run(
        self,
        prompt: str,
        initial_agent: Optional[Agent] = None,
        context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Run the network with a user prompt.
        
        Args:
            prompt: User prompt to process
            initial_agent: Optional specific agent to start with
            context: Additional context
            
        Returns:
            Network execution results
        """
        # Add initial user message
        self.state.add_message("user", prompt)
        
        # Track execution
        start_time = datetime.now()
        iterations = 0
        last_agent = None
        last_result = None
        agent_stack = []
        
        # Determine first agent
        if initial_agent:
            current_agent = initial_agent
        else:
            # Let router decide
            router_args = RouterArgs(
                network=self,
                state=self.state,
                stack=agent_stack,
                call_count=0,
                last_result=None,
                last_agent=None
            )
            current_agent = await self._route(router_args)
        
        # Main execution loop
        while current_agent and iterations < self.max_iterations:
            iterations += 1
            
            # Execute agent
            try:
                # Prepare agent context
                agent_context = {
                    "network": self,
                    "state": self.state,
                    "iteration": iterations,
                    **(context or {})
                }
                
                # Run agent
                result = await current_agent.run(
                    prompt=self._build_agent_prompt(current_agent, last_result),
                    state=self.state,
                    context=agent_context
                )
                
                # Store result
                self.state.set_agent_result(current_agent.name, result)
                
                # Add agent output to messages
                output = result.get("output", [])
                for item in output:
                    if item.get("type") == "text":
                        self.state.add_message(
                            "assistant",
                            item.get("content", ""),
                            agent_id=current_agent.name
                        )
                
                # Update tracking
                last_agent = current_agent
                last_result = result
                
                # Get next agent from router
                router_args = RouterArgs(
                    network=self,
                    state=self.state,
                    stack=agent_stack,
                    call_count=iterations,
                    last_result=result,
                    last_agent=current_agent
                )
                current_agent = await self._route(router_args)
                
            except Exception as e:
                # Handle errors
                self.state.add_message(
                    "system",
                    f"Error in {current_agent.name}: {str(e)}",
                    agent_id=current_agent.name
                )
                
                # Try to recover with router
                router_args = RouterArgs(
                    network=self,
                    state=self.state,
                    stack=agent_stack,
                    call_count=iterations,
                    last_result={"error": str(e)},
                    last_agent=current_agent
                )
                current_agent = await self._route(router_args)
        
        # Build final result
        end_time = datetime.now()
        duration = (end_time - start_time).total_seconds()
        
        return {
            "success": iterations < self.max_iterations,
            "iterations": iterations,
            "duration": duration,
            "final_output": self._get_final_output(),
            "agent_results": self.state.agent_results,
            "messages": [m.to_dict() for m in self.state.messages],
            "state": self.state.to_dict()
        }
    
    async def _route(self, args: RouterArgs) -> Optional[Agent]:
        """Execute router to get next agent.
        
        Args:
            args: Router arguments
            
        Returns:
            Next agent or None to stop
        """
        if isinstance(self.router, RoutingAgent):
            # LLM-based routing
            return await self.router.route(args)
        elif isinstance(self.router, Router):
            # Code-based router object
            return self.router(args)
        elif callable(self.router):
            # Raw function router
            return self.router(args)
        else:
            # No router - stop
            return None
    
    def _build_agent_prompt(
        self,
        agent: Agent,
        last_result: Optional[Dict[str, Any]]
    ) -> List[Any]:
        """Build prompt for agent including conversation history.
        
        Args:
            agent: Current agent
            last_result: Previous agent's result
            
        Returns:
            List of messages for agent
        """
        # Get recent messages
        messages = []
        
        # Include recent conversation
        for msg in self.state.messages[-10:]:  # Last 10 messages
            if msg.agent_id != agent.name:  # Don't include agent's own messages
                messages.append({
                    "role": msg.role,
                    "content": msg.content
                })
        
        return messages
    
    def _get_final_output(self) -> str:
        """Get the final output from the network execution."""
        # Find last assistant message
        for msg in reversed(self.state.messages):
            if msg.role == "assistant":
                return msg.content
        
        return "No output generated"
    
    def add_agent(self, agent: Agent) -> None:
        """Add an agent to the network.
        
        Args:
            agent: Agent to add
        """
        self.agents.append(agent)
        self.agent_map[agent.name] = agent
    
    def remove_agent(self, agent_name: str) -> None:
        """Remove an agent from the network.
        
        Args:
            agent_name: Name of agent to remove
        """
        self.agents = [a for a in self.agents if a.name != agent_name]
        self.agent_map.pop(agent_name, None)
    
    def get_agent(self, agent_name: str) -> Optional[Agent]:
        """Get an agent by name.
        
        Args:
            agent_name: Agent name
            
        Returns:
            Agent if found
        """
        return self.agent_map.get(agent_name)


def create_network(
    agents: List[Agent],
    name: Optional[str] = None,
    router: Optional[Union[Router, RouterFunction, RoutingAgent]] = None,
    default_model: Optional[str] = None,
    max_iterations: int = 10,
    default_state: Optional[NetworkState] = None,
    **metadata
) -> Network:
    """Create a network of agents.
    
    Args:
        agents: List of agents in the network
        name: Network name
        router: Router for agent orchestration
        default_model: Default model for routing
        max_iterations: Maximum execution iterations
        default_state: Initial state
        **metadata: Additional metadata
        
    Returns:
        Configured Network instance
    """
    config = NetworkConfig(
        name=name or "network",
        agents=agents,
        router=router,
        default_model=default_model,
        max_iterations=max_iterations,
        default_state=default_state,
        metadata=metadata
    )
    
    return Network(config)