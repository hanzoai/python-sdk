"""Network orchestration for agent execution."""

from typing import TypeVar, Generic, List, Type, Optional, Dict, Any, Union
import asyncio
from datetime import datetime
import json
from pathlib import Path
from prometheus_client import Counter, Histogram, Gauge
import structlog

from hanzo_agents.core.agent import Agent, InferenceResult, ToolCall
from hanzo_agents.core.state import State, StateGuard, StateHistory
from hanzo_agents.core.router import Router, RouterFn, DeterministicRouter
from hanzo_agents.core.history import History
from hanzo_agents.core.memory import MemoryKV, MemoryVector


S = TypeVar("S", bound=State)

# Metrics
router_iterations = Counter("hanzo_router_iterations_total", "Total router iterations")
agent_invocations = Counter("hanzo_agent_invocations_total", "Total agent invocations", ["agent"])
network_errors = Counter("hanzo_network_errors_total", "Total network errors", ["type"])
execution_time = Histogram("hanzo_execution_time_seconds", "Execution time", ["phase"])
active_networks = Gauge("hanzo_active_networks", "Number of active networks")

logger = structlog.get_logger()


class Network(Generic[S]):
    """Main orchestration class for agent networks.
    
    Responsibilities:
    1. Owns the state instance
    2. Executes the router after each agent call
    3. Maintains history
    4. Emits telemetry
    """
    
    def __init__(self,
                 *,
                 state: S,
                 agents: List[Type[Agent[S]]],
                 router: Union[Router, RouterFn[S]],
                 memory_kv: Optional[MemoryKV] = None,
                 memory_vector: Optional[MemoryVector] = None,
                 max_steps: int = 100,
                 checkpoint_dir: Optional[Path] = None):
        """Initialize network.
        
        Args:
            state: Initial state
            agents: Available agent types
            router: Router instance or function
            memory_kv: Optional KV store
            memory_vector: Optional vector store
            max_steps: Maximum execution steps
            checkpoint_dir: Directory for checkpoints
        """
        self.state = state
        self.agents = agents
        self.router = router if isinstance(router, Router) else DeterministicRouter(router)
        self.memory_kv = memory_kv
        self.memory_vector = memory_vector
        self.max_steps = max_steps
        self.checkpoint_dir = Path(checkpoint_dir) if checkpoint_dir else None
        
        # Runtime state
        self.history = History()
        self.state_history = StateHistory()
        self.call_count = 0
        self.last_result: Optional[InferenceResult] = None
        self._running = False
        self._agent_instances: Dict[str, Agent[S]] = {}
        
        # Record initial state
        self.state_history.record(state, "initial")
        
        # Metrics
        active_networks.inc()
    
    def __del__(self):
        """Cleanup on deletion."""
        active_networks.dec()
    
    async def run(self) -> S:
        """Execute the network until completion.
        
        Returns:
            Final state
        """
        if self._running:
            raise RuntimeError("Network already running")
        
        self._running = True
        start_time = datetime.utcnow()
        
        try:
            while self.call_count < self.max_steps:
                # Router decision
                with execution_time.labels(phase="routing").time():
                    next_agent_type = await self._route()
                
                if next_agent_type is None:
                    logger.info("Router returned None, stopping", call_count=self.call_count)
                    break
                
                # Execute agent
                with execution_time.labels(phase="agent").time():
                    result = await self._execute_agent(next_agent_type)
                
                self.last_result = result
                self.call_count += 1
                router_iterations.inc()
                
                # Checkpoint if configured
                if self.checkpoint_dir and self.call_count % 10 == 0:
                    await self._checkpoint()
            
            # Final checkpoint
            if self.checkpoint_dir:
                await self._checkpoint(final=True)
            
            duration = (datetime.utcnow() - start_time).total_seconds()
            logger.info(
                "Network execution completed",
                call_count=self.call_count,
                duration=duration,
                final_state=self.state.to_dict()
            )
            
        except Exception as e:
            network_errors.labels(type=type(e).__name__).inc()
            logger.error("Network execution failed", error=str(e), exc_info=True)
            raise
        finally:
            self._running = False
        
        return self.state
    
    async def _route(self) -> Optional[Type[Agent[S]]]:
        """Execute router to get next agent."""
        if hasattr(self.router, 'route_async'):
            return await self.router.route_async(
                self, self.call_count, self.last_result, self.agents
            )
        else:
            return self.router.route(
                self, self.call_count, self.last_result, self.agents
            )
    
    async def _execute_agent(self, agent_type: Type[Agent[S]]) -> InferenceResult:
        """Execute a single agent."""
        # Get or create agent instance
        agent_name = agent_type.name
        if agent_name not in self._agent_instances:
            self._agent_instances[agent_name] = agent_type()
        
        agent = self._agent_instances[agent_name]
        agent_invocations.labels(agent=agent_name).inc()
        
        logger.info("Executing agent", agent=agent_name, state=self.state.to_dict())
        
        try:
            # Run agent inference
            with StateGuard(self.state):
                result = await agent.run(self.state, self.history, self)
            
            # Record in history
            self.history.add_inference(result)
            
            # Execute any tool calls
            for tool_call in result.tool_calls:
                await self._execute_tool(agent, tool_call)
            
            # Record state change
            self.state_history.record(self.state, f"after_{agent_name}")
            
            return result
            
        except Exception as e:
            logger.error("Agent execution failed", agent=agent_name, error=str(e))
            raise
    
    async def _execute_tool(self, agent: Agent[S], tool_call: ToolCall):
        """Execute a tool call."""
        logger.info("Executing tool", tool=tool_call.tool, args=tool_call.arguments)
        
        try:
            # Execute tool
            result = await agent.execute_tool(tool_call.tool, tool_call.arguments, self)
            
            # Record result
            self.history.add_tool_result(tool_call.tool, result, agent.name)
            
            logger.info("Tool execution completed", tool=tool_call.tool, result=str(result)[:100])
            
        except Exception as e:
            logger.error("Tool execution failed", tool=tool_call.tool, error=str(e))
            self.history.add_tool_result(tool_call.tool, f"Error: {e}", agent.name)
    
    async def _checkpoint(self, final: bool = False):
        """Save checkpoint."""
        if not self.checkpoint_dir:
            return
        
        self.checkpoint_dir.mkdir(exist_ok=True)
        
        checkpoint_data = {
            "state": self.state.checkpoint(),
            "history": [entry.to_dict() for entry in self.history],
            "call_count": self.call_count,
            "timestamp": datetime.utcnow().isoformat(),
            "final": final
        }
        
        filename = f"checkpoint_{self.call_count:04d}.json"
        if final:
            filename = "checkpoint_final.json"
        
        path = self.checkpoint_dir / filename
        
        with open(path, 'w') as f:
            json.dump(checkpoint_data, f, indent=2)
        
        logger.info("Checkpoint saved", path=str(path))
    
    @classmethod
    async def restore(cls, checkpoint_path: Path, **kwargs) -> "Network[S]":
        """Restore network from checkpoint."""
        with open(checkpoint_path) as f:
            data = json.load(f)
        
        # Restore state
        state_class = kwargs.get("state_class", State)
        state = state_class.restore(data["state"])
        
        # Create network
        network = cls(state=state, **kwargs)
        
        # Restore history
        for entry_data in data["history"]:
            network.history.append(History.from_dict(entry_data))
        
        network.call_count = data["call_count"]
        
        logger.info("Network restored from checkpoint", path=str(checkpoint_path))
        
        return network