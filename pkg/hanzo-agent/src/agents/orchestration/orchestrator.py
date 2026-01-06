"""Main orchestrator for agent systems."""

from __future__ import annotations

import asyncio
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

from ..agent import Agent
from ..exceptions import AgentsException
from ..logger import logger
from ..network.network import AgentNetwork, NetworkConfig
from ..result import RunResult
from ..run_context import RunContextWrapper, TContext
from ..state.store import StateStore, InMemoryStateStore
from ..tracing import trace, custom_span
from .executor import WorkflowExecutor, ExecutionResult
from .ui_stream import UIStreamer
from .workflow import Workflow


@dataclass
class OrchestrationConfig:
    """Configuration for orchestration."""
    
    name: str = "Agent Orchestrator"
    """Name of the orchestrator."""
    
    enable_tracing: bool = True
    """Whether to enable detailed tracing."""
    
    enable_ui_streaming: bool = True
    """Whether to enable UI streaming updates."""
    
    max_concurrent_workflows: int = 10
    """Maximum number of concurrent workflows."""
    
    state_store: StateStore | None = None
    """State store for persistence."""
    
    retry_failed_steps: bool = True
    """Whether to retry failed workflow steps."""
    
    max_retries: int = 3
    """Maximum retries for failed steps."""


class Orchestrator:
    """High-level orchestrator for complex agent systems.
    
    This class provides:
    - Workflow management and execution
    - Network orchestration
    - UI streaming capabilities
    - Comprehensive tracing and debugging
    """
    
    def __init__(
        self,
        config: OrchestrationConfig | None = None,
        network: AgentNetwork | None = None,
    ):
        """Initialize orchestrator.
        
        Args:
            config: Orchestration configuration
            network: Agent network to use
        """
        self.config = config or OrchestrationConfig()
        self.network = network or AgentNetwork()
        self.workflows: Dict[str, Workflow] = {}
        self.executors: Dict[str, WorkflowExecutor] = {}
        self.ui_streamer = UIStreamer() if self.config.enable_ui_streaming else None
        self.state_store = self.config.state_store or InMemoryStateStore()
        self._semaphore = asyncio.Semaphore(self.config.max_concurrent_workflows)
        
    def register_workflow(self, workflow: Workflow) -> None:
        """Register a workflow with the orchestrator.
        
        Args:
            workflow: Workflow to register
        """
        if workflow.id in self.workflows:
            raise AgentsException(f"Workflow '{workflow.id}' already registered")
            
        self.workflows[workflow.id] = workflow
        logger.debug(f"Registered workflow: {workflow.id}")
        
    def register_agent(
        self,
        agent: Agent[TContext],
        capabilities: List[str] | None = None,
        metadata: Dict[str, Any] | None = None,
    ) -> None:
        """Register an agent with the network.
        
        Args:
            agent: Agent to register
            capabilities: Agent capabilities
            metadata: Additional metadata
        """
        self.network.add_agent(
            agent,
            capabilities=capabilities,
            metadata=metadata,
        )
        
    async def execute_workflow(
        self,
        workflow_id: str,
        input: Any,
        context: TContext | None = None,
        stream_updates: bool | None = None,
    ) -> ExecutionResult:
        """Execute a workflow.
        
        Args:
            workflow_id: ID of workflow to execute
            input: Input data for the workflow
            context: Execution context
            stream_updates: Whether to stream UI updates
            
        Returns:
            Execution result
        """
        if workflow_id not in self.workflows:
            raise AgentsException(f"Workflow '{workflow_id}' not found")
            
        workflow = self.workflows[workflow_id]
        
        # Use semaphore to limit concurrent workflows
        async with self._semaphore:
            # Create executor
            executor = WorkflowExecutor(
                workflow=workflow,
                network=self.network,
                state_store=self.state_store,
                retry_failed=self.config.retry_failed_steps,
                max_retries=self.config.max_retries,
            )
            
            # Store executor
            execution_id = executor.execution_id
            self.executors[execution_id] = executor
            
            # Set up UI streaming if enabled
            if stream_updates or (stream_updates is None and self.config.enable_ui_streaming):
                if self.ui_streamer:
                    executor.set_ui_streamer(self.ui_streamer)
                    
            # Execute with tracing
            trace_name = f"workflow_execution:{workflow.name}"
            
            with trace(trace_name, metadata={"workflow_id": workflow_id}):
                try:
                    result = await executor.execute(input, context)
                    return result
                finally:
                    # Clean up
                    del self.executors[execution_id]
                    
    async def execute_parallel_workflows(
        self,
        executions: List[Dict[str, Any]],
        context: TContext | None = None,
    ) -> List[ExecutionResult]:
        """Execute multiple workflows in parallel.
        
        Args:
            executions: List of execution specs with 'workflow_id' and 'input'
            context: Shared context
            
        Returns:
            List of execution results
        """
        tasks = []
        
        for spec in executions:
            task = self.execute_workflow(
                workflow_id=spec["workflow_id"],
                input=spec["input"],
                context=context,
                stream_updates=spec.get("stream_updates", True),
            )
            tasks.append(task)
            
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Handle exceptions
        final_results = []
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                logger.error(f"Workflow {executions[i]['workflow_id']} failed: {result}")
                # Create failed result
                final_results.append(ExecutionResult(
                    workflow_id=executions[i]["workflow_id"],
                    execution_id="failed",
                    success=False,
                    error=str(result),
                    steps_completed=0,
                    total_steps=0,
                ))
            else:
                final_results.append(result)
                
        return final_results
        
    async def run_agent(
        self,
        agent_name: str,
        input: Any,
        context: TContext | None = None,
        **kwargs,
    ) -> RunResult:
        """Run a single agent through the network.
        
        Args:
            agent_name: Name of agent to run
            input: Input for the agent
            context: Execution context
            **kwargs: Additional arguments for runner
            
        Returns:
            Agent run result
        """
        return await self.network.run(
            input=input,
            starting_agent=agent_name,
            context=context,
            **kwargs,
        )
        
    def create_workflow_from_agents(
        self,
        name: str,
        agents: List[str],
        parallel: bool = False,
    ) -> Workflow:
        """Create a workflow from a list of agents.
        
        Args:
            name: Workflow name
            agents: List of agent names
            parallel: Whether to run agents in parallel
            
        Returns:
            Created workflow
        """
        workflow = Workflow(name=name)
        
        if parallel:
            # Create parallel execution
            parallel_agents = []
            for agent_name in agents:
                step = workflow.add_agent_step(
                    name=f"Run {agent_name}",
                    agent_name=agent_name,
                )
                parallel_agents.append(step.id)
                
            # Mark as parallel
            for step_id in parallel_agents[1:]:
                workflow.steps[step_id].depends_on = []
                
        else:
            # Create sequential execution
            for agent_name in agents:
                workflow.add_agent_step(
                    name=f"Run {agent_name}",
                    agent_name=agent_name,
                )
                
        return workflow
        
    def get_execution_status(self, execution_id: str) -> Dict[str, Any] | None:
        """Get status of a running execution.
        
        Args:
            execution_id: Execution ID
            
        Returns:
            Status information or None if not found
        """
        executor = self.executors.get(execution_id)
        
        if not executor:
            return None
            
        return executor.get_status()
        
    async def stream_updates(self, execution_id: str | None = None):
        """Stream UI updates for executions.
        
        Args:
            execution_id: Specific execution to stream, or None for all
            
        Yields:
            Stream updates
        """
        if not self.ui_streamer:
            return
            
        async for update in self.ui_streamer.stream(execution_id):
            yield update
            
    def visualize_workflow(self, workflow_id: str) -> str:
        """Generate a visual representation of a workflow.
        
        Args:
            workflow_id: Workflow to visualize
            
        Returns:
            Mermaid diagram string
        """
        if workflow_id not in self.workflows:
            raise AgentsException(f"Workflow '{workflow_id}' not found")
            
        workflow = self.workflows[workflow_id]
        return workflow.to_mermaid()
        
    async def get_state(self, key: str, namespace: str | None = None) -> Any:
        """Get a value from the state store."""
        return await self.state_store.get(key, namespace)
        
    async def set_state(self, key: str, value: Any, namespace: str | None = None) -> None:
        """Set a value in the state store."""
        await self.state_store.set(key, value, namespace)