"""Workflow execution engine."""

from __future__ import annotations

import asyncio
import time
import uuid
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

from ..exceptions import AgentsException
from ..logger import logger
from ..network.network import AgentNetwork
from ..result import RunResult
from ..run_context import RunContextWrapper, TContext
from ..state.store import StateStore
from ..tracing import custom_span
from .ui_stream import UIStreamer, StreamUpdate, UpdateType
from .workflow import Workflow, WorkflowStep, StepType


@dataclass
class StepResult:
    """Result of a workflow step execution."""
    
    step_id: str
    success: bool
    output: Any = None
    error: str | None = None
    start_time: float = field(default_factory=time.time)
    end_time: float | None = None
    retries: int = 0
    
    @property
    def duration(self) -> float:
        """Get execution duration."""
        if self.end_time:
            return self.end_time - self.start_time
        return 0.0


@dataclass
class ExecutionResult:
    """Result of a workflow execution."""
    
    workflow_id: str
    execution_id: str
    success: bool
    output: Any = None
    error: str | None = None
    steps_completed: int = 0
    total_steps: int = 0
    step_results: Dict[str, StepResult] = field(default_factory=dict)
    start_time: float = field(default_factory=time.time)
    end_time: float | None = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    @property
    def duration(self) -> float:
        """Get execution duration."""
        if self.end_time:
            return self.end_time - self.start_time
        return 0.0


class WorkflowExecutor:
    """Executes workflows with proper orchestration."""
    
    def __init__(
        self,
        workflow: Workflow,
        network: AgentNetwork,
        state_store: StateStore | None = None,
        retry_failed: bool = True,
        max_retries: int = 3,
    ):
        """Initialize executor.
        
        Args:
            workflow: Workflow to execute
            network: Agent network
            state_store: State store for persistence
            retry_failed: Whether to retry failed steps
            max_retries: Maximum retries per step
        """
        self.workflow = workflow
        self.network = network
        self.state_store = state_store
        self.retry_failed = retry_failed
        self.max_retries = max_retries
        self.execution_id = str(uuid.uuid4())
        self.ui_streamer: UIStreamer | None = None
        self._step_outputs: Dict[str, Any] = {}
        self._completed_steps: set[str] = set()
        
    def set_ui_streamer(self, streamer: UIStreamer) -> None:
        """Set UI streamer for updates."""
        self.ui_streamer = streamer
        
    async def execute(
        self,
        input: Any,
        context: TContext | None = None,
    ) -> ExecutionResult:
        """Execute the workflow.
        
        Args:
            input: Initial input data
            context: Execution context
            
        Returns:
            Execution result
        """
        # Validate workflow
        errors = self.workflow.validate()
        if errors:
            return ExecutionResult(
                workflow_id=self.workflow.id,
                execution_id=self.execution_id,
                success=False,
                error=f"Workflow validation failed: {'; '.join(errors)}",
                total_steps=len(self.workflow.steps),
            )
            
        # Initialize result
        result = ExecutionResult(
            workflow_id=self.workflow.id,
            execution_id=self.execution_id,
            success=True,
            total_steps=len(self.workflow.steps),
        )
        
        # Create execution context
        exec_context = ExecutionContext(
            input=input,
            context=context,
            executor=self,
        )
        
        # Send start update
        await self._send_update(
            UpdateType.WORKFLOW_START,
            {
                "workflow_id": self.workflow.id,
                "workflow_name": self.workflow.name,
                "total_steps": len(self.workflow.steps),
            },
        )
        
        try:
            # Get execution order
            execution_batches = self.workflow.get_execution_order()
            
            # Execute batches
            for batch in execution_batches:
                # Execute steps in parallel within batch
                batch_tasks = []
                
                for step_id in batch:
                    if step_id in self._completed_steps:
                        continue
                        
                    step = self.workflow.steps[step_id]
                    task = self._execute_step(step, exec_context, result)
                    batch_tasks.append(task)
                    
                # Wait for batch to complete
                if batch_tasks:
                    await asyncio.gather(*batch_tasks, return_exceptions=True)
                    
            # Set final output
            if self.workflow.entry_point:
                result.output = self._step_outputs.get(self.workflow.entry_point)
                
        except Exception as e:
            logger.error(f"Workflow execution failed: {e}")
            result.success = False
            result.error = str(e)
            
        finally:
            result.end_time = time.time()
            result.steps_completed = len(self._completed_steps)
            
            # Send completion update
            await self._send_update(
                UpdateType.WORKFLOW_COMPLETE,
                {
                    "success": result.success,
                    "duration": result.duration,
                    "steps_completed": result.steps_completed,
                    "error": result.error,
                },
            )
            
        return result
        
    async def _execute_step(
        self,
        step: WorkflowStep,
        context: ExecutionContext,
        result: ExecutionResult,
    ) -> None:
        """Execute a single step."""
        step_result = StepResult(step_id=step.id)
        
        # Send step start update
        await self._send_update(
            UpdateType.STEP_START,
            {
                "step_id": step.id,
                "step_name": step.name,
                "step_type": step.type.value,
            },
        )
        
        try:
            # Execute based on step type
            if step.type == StepType.AGENT:
                output = await self._execute_agent_step(step, context)
            elif step.type == StepType.PARALLEL:
                output = await self._execute_parallel_step(step, context)
            elif step.type == StepType.CONDITIONAL:
                output = await self._execute_conditional_step(step, context)
            elif step.type == StepType.LOOP:
                output = await self._execute_loop_step(step, context)
            elif step.type == StepType.TRANSFORM:
                output = await self._execute_transform_step(step, context)
            elif step.type == StepType.WAIT:
                output = await self._execute_wait_step(step, context)
            else:
                raise AgentsException(f"Unknown step type: {step.type}")
                
            # Store output
            self._step_outputs[step.id] = output
            self._completed_steps.add(step.id)
            
            step_result.success = True
            step_result.output = output
            
        except Exception as e:
            logger.error(f"Step {step.id} failed: {e}")
            step_result.success = False
            step_result.error = str(e)
            
            # Retry if configured
            if self.retry_failed and step_result.retries < self.max_retries:
                step_result.retries += 1
                logger.info(f"Retrying step {step.id} (attempt {step_result.retries})")
                
                # Recursive retry
                await asyncio.sleep(2 ** step_result.retries)  # Exponential backoff
                await self._execute_step(step, context, result)
                return
                
            # Handle error step
            if step.on_error and step.on_error in self.workflow.steps:
                error_step = self.workflow.steps[step.on_error]
                await self._execute_step(error_step, context, result)
                
        finally:
            step_result.end_time = time.time()
            result.step_results[step.id] = step_result
            
            # Send step complete update
            await self._send_update(
                UpdateType.STEP_COMPLETE,
                {
                    "step_id": step.id,
                    "success": step_result.success,
                    "duration": step_result.duration,
                    "error": step_result.error,
                },
            )
            
    async def _execute_agent_step(
        self,
        step: WorkflowStep,
        context: ExecutionContext,
    ) -> Any:
        """Execute an agent step."""
        config = step.config
        agent_name = config["agent_name"]
        
        # Get input
        step_input = context.get_step_input(step.id)
        
        # Apply input transform if provided
        if transform := config.get("input_transform"):
            step_input = transform(step_input)
            
        # Run agent
        with custom_span("workflow_agent_step", {"agent": agent_name}):
            result = await self.network.run(
                input=step_input,
                starting_agent=agent_name,
                context=context.context,
            )
            
        # Extract output
        output = result.final_output
        
        # Apply output transform if provided
        if transform := config.get("output_transform"):
            output = transform(output)
            
        return output
        
    async def _execute_parallel_step(
        self,
        step: WorkflowStep,
        context: ExecutionContext,
    ) -> List[Any]:
        """Execute parallel steps."""
        step_ids = step.config["step_ids"]
        
        # Execute sub-steps in parallel
        tasks = []
        for step_id in step_ids:
            if step_id in self.workflow.steps:
                sub_step = self.workflow.steps[step_id]
                task = self._execute_step(sub_step, context, None)
                tasks.append(task)
                
        # Wait for all to complete
        await asyncio.gather(*tasks, return_exceptions=True)
        
        # Collect outputs
        outputs = []
        for step_id in step_ids:
            if step_id in self._step_outputs:
                outputs.append(self._step_outputs[step_id])
                
        return outputs
        
    async def _execute_conditional_step(
        self,
        step: WorkflowStep,
        context: ExecutionContext,
    ) -> Any:
        """Execute conditional step."""
        condition = step.config["condition"]
        if_true = step.config["if_true"]
        if_false = step.config.get("if_false")
        
        # Evaluate condition
        step_input = context.get_step_input(step.id)
        
        if callable(condition):
            result = condition(step_input)
        else:
            # Simple expression evaluation
            result = eval(condition, {"input": step_input})
            
        # Execute appropriate branch
        if result and if_true in self.workflow.steps:
            branch_step = self.workflow.steps[if_true]
            await self._execute_step(branch_step, context, None)
            return self._step_outputs.get(if_true)
        elif not result and if_false and if_false in self.workflow.steps:
            branch_step = self.workflow.steps[if_false]
            await self._execute_step(branch_step, context, None)
            return self._step_outputs.get(if_false)
            
        return None
        
    async def _execute_loop_step(
        self,
        step: WorkflowStep,
        context: ExecutionContext,
    ) -> List[Any]:
        """Execute loop step."""
        over = step.config["over"]
        body = step.config["body"]
        max_iterations = step.config.get("max_iterations")
        
        # Get items to loop over
        step_input = context.get_step_input(step.id)
        
        if callable(over):
            items = over(step_input)
        else:
            # Simple path evaluation
            items = eval(f"input.{over}", {"input": step_input})
            
        # Limit iterations
        if max_iterations:
            items = items[:max_iterations]
            
        # Execute body for each item
        outputs = []
        
        for i, item in enumerate(items):
            if body in self.workflow.steps:
                # Set loop context
                context.set_loop_item(item, i)
                
                body_step = self.workflow.steps[body]
                await self._execute_step(body_step, context, None)
                
                if body in self._step_outputs:
                    outputs.append(self._step_outputs[body])
                    
        return outputs
        
    async def _execute_transform_step(
        self,
        step: WorkflowStep,
        context: ExecutionContext,
    ) -> Any:
        """Execute transform step."""
        transform = step.config["transform"]
        step_input = context.get_step_input(step.id)
        
        if callable(transform):
            return transform(step_input)
        else:
            raise AgentsException("Transform must be a callable")
            
    async def _execute_wait_step(
        self,
        step: WorkflowStep,
        context: ExecutionContext,
    ) -> None:
        """Execute wait step."""
        # Simple timeout wait for now
        timeout = step.config.get("timeout", 1.0)
        await asyncio.sleep(timeout)
        
    async def _send_update(self, type: UpdateType, data: Dict[str, Any]) -> None:
        """Send update to UI streamer."""
        if self.ui_streamer:
            update = StreamUpdate(
                execution_id=self.execution_id,
                type=type,
                data=data,
            )
            await self.ui_streamer.send(update)
            
    def get_status(self) -> Dict[str, Any]:
        """Get current execution status."""
        return {
            "execution_id": self.execution_id,
            "workflow_id": self.workflow.id,
            "workflow_name": self.workflow.name,
            "steps_completed": len(self._completed_steps),
            "total_steps": len(self.workflow.steps),
            "completed_steps": list(self._completed_steps),
            "outputs": self._step_outputs,
        }


@dataclass
class ExecutionContext:
    """Context for workflow execution."""
    
    input: Any
    context: TContext | None
    executor: WorkflowExecutor
    _loop_item: Any = None
    _loop_index: int = 0
    
    def get_step_input(self, step_id: str) -> Any:
        """Get input for a step."""
        step = self.executor.workflow.steps[step_id]
        
        # If step has dependencies, use their outputs
        if step.depends_on:
            # Single dependency: use its output directly
            if len(step.depends_on) == 1:
                dep_id = step.depends_on[0]
                if dep_id in self.executor._step_outputs:
                    return self.executor._step_outputs[dep_id]
                    
            # Multiple dependencies: collect as list
            else:
                outputs = []
                for dep_id in step.depends_on:
                    if dep_id in self.executor._step_outputs:
                        outputs.append(self.executor._step_outputs[dep_id])
                return outputs
                
        # Check if in loop context
        if self._loop_item is not None:
            return self._loop_item
            
        # Default to workflow input
        return self.input
        
    def set_loop_item(self, item: Any, index: int) -> None:
        """Set current loop item."""
        self._loop_item = item
        self._loop_index = index