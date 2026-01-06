"""Agent network implementation for multi-agent orchestration."""

from __future__ import annotations

import asyncio
import dataclasses
from dataclasses import dataclass, field
from typing import Any, Callable, Dict, List, Optional, Type, cast

from ..agent import Agent
from ..exceptions import AgentsException
from ..handoffs import Handoff, handoff
from ..items import TResponseInputItem
from ..lifecycle import RunHooks
from ..logger import logger
from ..result import RunResult
from ..run import Runner, RunConfig
from ..run_context import RunContextWrapper, TContext
from ..state.store import StateStore, InMemoryStateStore
from ..tracing import custom_span, get_current_trace
from .node import NetworkNode, NodeStatus
from .router import Router, RoutingDecision, SemanticRouter


@dataclass
class NetworkConfig:
    """Configuration for an agent network."""
    
    name: str = "Agent Network"
    """Name of the network for tracing and logging."""
    
    default_model: str = "gpt-3.5-turbo"
    """Default model to use for agents in the network."""
    
    state_store: StateStore | None = None
    """State store for sharing data between agents. Defaults to InMemoryStateStore."""
    
    enable_parallel_execution: bool = True
    """Whether to enable parallel execution of independent agents."""
    
    max_parallel_agents: int = 5
    """Maximum number of agents that can run in parallel."""
    
    enable_tracing: bool = True
    """Whether to enable detailed network tracing."""
    
    retry_failed_nodes: bool = True
    """Whether to retry failed agent nodes."""
    
    max_retries: int = 3
    """Maximum number of retries for failed nodes."""


class AgentNetwork:
    """A network of agents that can collaborate and share state.
    
    This class provides a way to organize agents into a network where they can:
    - Share state through a common state store
    - Route tasks intelligently using routers
    - Execute in parallel when possible
    - Handle failures gracefully
    """
    
    def __init__(
        self,
        config: NetworkConfig | None = None,
        router: Router | None = None,
    ):
        """Initialize an agent network.
        
        Args:
            config: Network configuration
            router: Router for intelligent task routing
        """
        self.config = config or NetworkConfig()
        self.router = router or SemanticRouter()
        self.nodes: Dict[str, NetworkNode] = {}
        self.state_store = self.config.state_store or InMemoryStateStore()
        self._lock = asyncio.Lock()
        
    def add_agent(
        self,
        agent: Agent[TContext],
        *,
        capabilities: List[str] | None = None,
        dependencies: List[str] | None = None,
        metadata: Dict[str, Any] | None = None,
    ) -> NetworkNode:
        """Add an agent to the network.
        
        Args:
            agent: The agent to add
            capabilities: List of capabilities this agent provides
            dependencies: List of agent names this agent depends on
            metadata: Additional metadata for routing decisions
            
        Returns:
            The network node wrapping the agent
        """
        if agent.name in self.nodes:
            raise AgentsException(f"Agent '{agent.name}' already exists in network")
            
        node = NetworkNode(
            agent=agent,
            capabilities=capabilities or [],
            dependencies=dependencies or [],
            metadata=metadata or {},
        )
        
        self.nodes[agent.name] = node
        
        # Update router with new agent information
        self.router.update_agent_info(agent.name, node.capabilities, node.metadata)
        
        logger.debug(f"Added agent '{agent.name}' to network with capabilities: {node.capabilities}")
        
        return node
        
    def remove_agent(self, agent_name: str) -> None:
        """Remove an agent from the network."""
        if agent_name not in self.nodes:
            raise AgentsException(f"Agent '{agent_name}' not found in network")
            
        del self.nodes[agent_name]
        self.router.remove_agent_info(agent_name)
        
        logger.debug(f"Removed agent '{agent_name}' from network")
        
    async def run(
        self,
        input: str | list[TResponseInputItem],
        *,
        starting_agent: str | None = None,
        context: TContext | None = None,
        max_turns: int = 10,
        hooks: RunHooks[TContext] | None = None,
        run_config: RunConfig | None = None,
    ) -> RunResult:
        """Run the network with the given input.
        
        Args:
            input: Initial input to the network
            starting_agent: Name of the agent to start with (if None, router decides)
            context: Shared context for all agents
            max_turns: Maximum number of agent turns
            hooks: Lifecycle hooks
            run_config: Run configuration
            
        Returns:
            Result of the network execution
        """
        async with self._lock:
            # Reset node statuses
            for node in self.nodes.values():
                node.status = NodeStatus.PENDING
                node.error = None
                
        # Create network context wrapper
        network_context = NetworkContextWrapper(
            context=context,
            state_store=self.state_store,
            network=self,
        )
        
        # Determine starting agent
        if starting_agent:
            if starting_agent not in self.nodes:
                raise AgentsException(f"Starting agent '{starting_agent}' not found in network")
            agent = self.nodes[starting_agent].agent
        else:
            # Use router to determine starting agent
            decision = await self.router.route(
                input=input,
                available_agents=list(self.nodes.keys()),
                context=network_context,
            )
            
            if not decision.selected_agent:
                raise AgentsException("Router could not determine starting agent")
                
            agent = self.nodes[decision.selected_agent].agent
            logger.debug(f"Router selected starting agent: {decision.selected_agent} (confidence: {decision.confidence})")
            
        # Create network-aware handoffs
        network_handoffs = self._create_network_handoffs(agent.name)
        
        # Clone agent with network handoffs
        network_agent = agent.clone(
            handoffs=list(agent.handoffs) + network_handoffs,
        )
        
        # Run with network context
        with custom_span("network_execution", {"network": self.config.name}):
            result = await Runner.run(
                starting_agent=network_agent,
                input=input,
                context=network_context,  # type: ignore
                max_turns=max_turns,
                hooks=hooks or NetworkHooks(self),
                run_config=run_config,
            )
            
        return result
        
    async def run_parallel(
        self,
        tasks: List[Dict[str, Any]],
        *,
        context: TContext | None = None,
        run_config: RunConfig | None = None,
    ) -> List[RunResult]:
        """Run multiple tasks in parallel across the network.
        
        Args:
            tasks: List of tasks, each with 'input' and optional 'agent' keys
            context: Shared context
            run_config: Run configuration
            
        Returns:
            List of results for each task
        """
        if not self.config.enable_parallel_execution:
            # Fall back to sequential execution
            results = []
            for task in tasks:
                result = await self.run(
                    input=task["input"],
                    starting_agent=task.get("agent"),
                    context=context,
                    run_config=run_config,
                )
                results.append(result)
            return results
            
        # Create tasks for parallel execution
        semaphore = asyncio.Semaphore(self.config.max_parallel_agents)
        
        async def run_task(task: Dict[str, Any]) -> RunResult:
            async with semaphore:
                return await self.run(
                    input=task["input"],
                    starting_agent=task.get("agent"),
                    context=context,
                    run_config=run_config,
                )
                
        # Run all tasks in parallel
        results = await asyncio.gather(
            *[run_task(task) for task in tasks],
            return_exceptions=True,
        )
        
        # Handle any exceptions
        final_results = []
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                logger.error(f"Task {i} failed: {result}")
                if self.config.retry_failed_nodes:
                    # Retry failed task
                    retry_result = await self.run(
                        input=tasks[i]["input"],
                        starting_agent=tasks[i].get("agent"),
                        context=context,
                        run_config=run_config,
                    )
                    final_results.append(retry_result)
                else:
                    raise result
            else:
                final_results.append(result)
                
        return final_results
        
    def _create_network_handoffs(self, current_agent: str) -> List[Handoff]:
        """Create handoffs to other agents in the network."""
        handoffs = []
        
        for name, node in self.nodes.items():
            if name == current_agent:
                continue
                
            # Create a dynamic handoff with network routing
            async def make_handoff_filter(target_name: str):
                async def network_handoff_filter(
                    ctx: RunContextWrapper[Any],
                    messages: List[TResponseInputItem],
                ) -> List[TResponseInputItem]:
                    # Use router to validate handoff
                    decision = await self.router.route(
                        input=messages,
                        available_agents=[target_name],
                        context=ctx,
                    )
                    
                    if decision.selected_agent == target_name:
                        # Add routing metadata
                        if messages and isinstance(messages[-1], dict):
                            messages[-1]["__network_routing__"] = {
                                "from": current_agent,
                                "to": target_name,
                                "confidence": decision.confidence,
                                "reason": decision.reason,
                            }
                            
                    return messages
                    
                return network_handoff_filter
                
            handoff = Handoff(
                agent=node.agent,
                input_filter=make_handoff_filter(name),
            )
            handoffs.append(handoff)
            
        return handoffs


class NetworkContextWrapper(RunContextWrapper):
    """Context wrapper that provides access to network state."""
    
    def __init__(
        self,
        context: TContext | None,
        state_store: StateStore,
        network: AgentNetwork,
    ):
        super().__init__(context)
        self.state_store = state_store
        self.network = network
        
    async def get_state(self, key: str, namespace: str | None = None) -> Any:
        """Get a value from the shared state store."""
        return await self.state_store.get(key, namespace)
        
    async def set_state(self, key: str, value: Any, namespace: str | None = None) -> None:
        """Set a value in the shared state store."""
        await self.state_store.set(key, value, namespace)
        
    async def update_state(self, key: str, updater: Callable[[Any], Any], namespace: str | None = None) -> Any:
        """Update a value in the shared state store."""
        return await self.state_store.update(key, updater, namespace)
        
    def get_network_info(self) -> Dict[str, Any]:
        """Get information about the network."""
        return {
            "name": self.network.config.name,
            "agents": list(self.network.nodes.keys()),
            "total_agents": len(self.network.nodes),
            "parallel_enabled": self.network.config.enable_parallel_execution,
        }


class NetworkHooks(RunHooks):
    """Hooks for network execution tracking."""
    
    def __init__(self, network: AgentNetwork):
        self.network = network
        
    async def on_agent_start(self, context: RunContextWrapper[Any], agent: Agent[Any]) -> None:
        """Called when an agent starts execution."""
        if agent.name in self.network.nodes:
            node = self.network.nodes[agent.name]
            node.status = NodeStatus.RUNNING
            node.execution_count += 1
            
            logger.debug(f"Network agent '{agent.name}' started (execution #{node.execution_count})")
            
    async def on_agent_end(self, context: RunContextWrapper[Any], agent: Agent[Any]) -> None:
        """Called when an agent ends execution."""
        if agent.name in self.network.nodes:
            node = self.network.nodes[agent.name]
            node.status = NodeStatus.COMPLETED
            
            logger.debug(f"Network agent '{agent.name}' completed")


def create_network(
    agents: List[Agent],
    router: Router | None = None,
    state_store: StateStore | None = None,
    default_model: str = "gpt-3.5-turbo",
    name: str = "default_network",
    enable_parallel_execution: bool = True,
) -> AgentNetwork:
    """Create a new agent network.
    
    Args:
        agents: List of agents to include in the network
        router: Router to use for agent selection
        state_store: State store for shared state
        default_model: Default model to use
        name: Name of the network
        enable_parallel_execution: Whether to enable parallel execution
        
    Returns:
        AgentNetwork instance
    """
    if router is None:
        from .router import SemanticRouter
        router = SemanticRouter()
        
    if state_store is None:
        from ..state import InMemoryStateStore
        state_store = InMemoryStateStore()
    
    config = NetworkConfig(
        name=name,
        default_model=default_model,
        state_store=state_store,
        enable_parallel_execution=enable_parallel_execution,
    )
    
    network = AgentNetwork(config=config, router=router)
    
    # Add all agents to the network
    for agent in agents:
        network.add_agent(agent)
        
    return network