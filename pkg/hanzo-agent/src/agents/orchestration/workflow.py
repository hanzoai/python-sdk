"""Workflow definition for orchestration."""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional, Callable

from ..exceptions import AgentsException


class StepType(Enum):
    """Type of workflow step."""
    
    AGENT = "agent"
    """Run an agent."""
    
    PARALLEL = "parallel"
    """Run multiple steps in parallel."""
    
    CONDITIONAL = "conditional"
    """Conditional branching."""
    
    LOOP = "loop"
    """Loop over items."""
    
    TRANSFORM = "transform"
    """Data transformation."""
    
    WAIT = "wait"
    """Wait for condition or timeout."""


@dataclass
class WorkflowStep:
    """A single step in a workflow."""
    
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    """Unique ID for the step."""
    
    name: str = ""
    """Human-readable name."""
    
    type: StepType = StepType.AGENT
    """Type of step."""
    
    config: Dict[str, Any] = field(default_factory=dict)
    """Step configuration."""
    
    depends_on: List[str] = field(default_factory=list)
    """IDs of steps this depends on."""
    
    retry_config: Dict[str, Any] = field(default_factory=dict)
    """Retry configuration for this step."""
    
    timeout: float | None = None
    """Timeout in seconds."""
    
    on_error: str | None = None
    """Step to run on error."""
    
    metadata: Dict[str, Any] = field(default_factory=dict)
    """Additional metadata."""


class Workflow:
    """A workflow definition."""
    
    def __init__(
        self,
        name: str,
        description: str = "",
        version: str = "1.0.0",
    ):
        """Initialize workflow.
        
        Args:
            name: Workflow name
            description: Workflow description
            version: Workflow version
        """
        self.id = str(uuid.uuid4())
        self.name = name
        self.description = description
        self.version = version
        self.steps: Dict[str, WorkflowStep] = {}
        self.entry_point: str | None = None
        self.metadata: Dict[str, Any] = {}
        
    def add_step(self, step: WorkflowStep) -> WorkflowStep:
        """Add a step to the workflow.
        
        Args:
            step: Step to add
            
        Returns:
            The added step
        """
        if step.id in self.steps:
            raise AgentsException(f"Step '{step.id}' already exists")
            
        self.steps[step.id] = step
        
        # Set as entry point if first step
        if self.entry_point is None:
            self.entry_point = step.id
            
        return step
        
    def add_agent_step(
        self,
        name: str,
        agent_name: str,
        input_transform: Callable[[Any], Any] | None = None,
        output_transform: Callable[[Any], Any] | None = None,
        **kwargs,
    ) -> WorkflowStep:
        """Add an agent execution step.
        
        Args:
            name: Step name
            agent_name: Name of agent to run
            input_transform: Optional input transformation
            output_transform: Optional output transformation
            **kwargs: Additional step configuration
            
        Returns:
            The created step
        """
        config = {
            "agent_name": agent_name,
            "input_transform": input_transform,
            "output_transform": output_transform,
        }
        config.update(kwargs)
        
        step = WorkflowStep(
            name=name,
            type=StepType.AGENT,
            config=config,
        )
        
        # Auto-depend on previous step if exists
        if self.steps:
            last_step_id = list(self.steps.keys())[-1]
            step.depends_on = [last_step_id]
            
        return self.add_step(step)
        
    def add_parallel_step(
        self,
        name: str,
        steps: List[WorkflowStep],
    ) -> WorkflowStep:
        """Add a parallel execution step.
        
        Args:
            name: Step name
            steps: Steps to run in parallel
            
        Returns:
            The created parallel step
        """
        # Add sub-steps first
        step_ids = []
        for sub_step in steps:
            self.add_step(sub_step)
            step_ids.append(sub_step.id)
            
        # Create parallel container
        parallel_step = WorkflowStep(
            name=name,
            type=StepType.PARALLEL,
            config={"step_ids": step_ids},
        )
        
        return self.add_step(parallel_step)
        
    def add_conditional_step(
        self,
        name: str,
        condition: Callable[[Any], bool] | str,
        if_true: str,
        if_false: str | None = None,
    ) -> WorkflowStep:
        """Add a conditional branching step.
        
        Args:
            name: Step name
            condition: Condition function or expression
            if_true: Step ID to run if true
            if_false: Step ID to run if false
            
        Returns:
            The created conditional step
        """
        step = WorkflowStep(
            name=name,
            type=StepType.CONDITIONAL,
            config={
                "condition": condition,
                "if_true": if_true,
                "if_false": if_false,
            },
        )
        
        return self.add_step(step)
        
    def add_loop_step(
        self,
        name: str,
        over: str | Callable[[Any], List[Any]],
        body: str,
        max_iterations: int | None = None,
    ) -> WorkflowStep:
        """Add a loop step.
        
        Args:
            name: Step name
            over: Data path or function to get items
            body: Step ID to run for each item
            max_iterations: Maximum iterations
            
        Returns:
            The created loop step
        """
        step = WorkflowStep(
            name=name,
            type=StepType.LOOP,
            config={
                "over": over,
                "body": body,
                "max_iterations": max_iterations,
            },
        )
        
        return self.add_step(step)
        
    def add_transform_step(
        self,
        name: str,
        transform: Callable[[Any], Any],
    ) -> WorkflowStep:
        """Add a data transformation step.
        
        Args:
            name: Step name
            transform: Transformation function
            
        Returns:
            The created transform step
        """
        step = WorkflowStep(
            name=name,
            type=StepType.TRANSFORM,
            config={"transform": transform},
        )
        
        return self.add_step(step)
        
    def get_execution_order(self) -> List[List[str]]:
        """Get the execution order respecting dependencies.
        
        Returns:
            List of step ID batches that can run in parallel
        """
        if not self.steps:
            return []
            
        # Topological sort with batching
        visited = set()
        in_degree = {step_id: len(step.depends_on) for step_id, step in self.steps.items()}
        
        batches = []
        
        while len(visited) < len(self.steps):
            # Find all steps with no remaining dependencies
            batch = []
            for step_id, degree in in_degree.items():
                if step_id not in visited and degree == 0:
                    batch.append(step_id)
                    visited.add(step_id)
                    
            if not batch:
                # Circular dependency
                raise AgentsException("Circular dependency detected in workflow")
                
            batches.append(batch)
            
            # Update in-degrees
            for step_id in batch:
                # Find steps that depend on this one
                for other_id, other_step in self.steps.items():
                    if step_id in other_step.depends_on:
                        in_degree[other_id] -= 1
                        
        return batches
        
    def validate(self) -> List[str]:
        """Validate the workflow.
        
        Returns:
            List of validation errors (empty if valid)
        """
        errors = []
        
        # Check entry point
        if not self.entry_point:
            errors.append("No entry point defined")
        elif self.entry_point not in self.steps:
            errors.append(f"Entry point '{self.entry_point}' not found")
            
        # Check dependencies
        for step_id, step in self.steps.items():
            for dep_id in step.depends_on:
                if dep_id not in self.steps:
                    errors.append(f"Step '{step_id}' depends on unknown step '{dep_id}'")
                    
        # Check step configurations
        for step_id, step in self.steps.items():
            if step.type == StepType.AGENT:
                if "agent_name" not in step.config:
                    errors.append(f"Agent step '{step_id}' missing agent_name")
            elif step.type == StepType.CONDITIONAL:
                if "condition" not in step.config:
                    errors.append(f"Conditional step '{step_id}' missing condition")
                if "if_true" not in step.config:
                    errors.append(f"Conditional step '{step_id}' missing if_true")
                    
        # Try to get execution order (checks for cycles)
        try:
            self.get_execution_order()
        except AgentsException as e:
            errors.append(str(e))
            
        return errors
        
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary representation."""
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "version": self.version,
            "entry_point": self.entry_point,
            "steps": {
                step_id: {
                    "id": step.id,
                    "name": step.name,
                    "type": step.type.value,
                    "config": step.config,
                    "depends_on": step.depends_on,
                    "retry_config": step.retry_config,
                    "timeout": step.timeout,
                    "on_error": step.on_error,
                    "metadata": step.metadata,
                }
                for step_id, step in self.steps.items()
            },
            "metadata": self.metadata,
        }
        
    def to_mermaid(self) -> str:
        """Generate Mermaid diagram of the workflow."""
        lines = ["graph TD"]
        
        # Add nodes
        for step_id, step in self.steps.items():
            label = step.name or step_id[:8]
            shape = {
                StepType.AGENT: f"{step_id}[{label}]",
                StepType.PARALLEL: f"{step_id}{{{{{label}}}}}",
                StepType.CONDITIONAL: f"{step_id}{{{label}}}",
                StepType.LOOP: f"{step_id}(({label}))",
                StepType.TRANSFORM: f"{step_id}[/{label}/]",
                StepType.WAIT: f"{step_id}[({label})]",
            }
            lines.append(f"    {shape.get(step.type, f'{step_id}[{label}]')}")
            
        # Add edges
        for step_id, step in self.steps.items():
            for dep_id in step.depends_on:
                lines.append(f"    {dep_id} --> {step_id}")
                
        # Add conditional branches
        for step_id, step in self.steps.items():
            if step.type == StepType.CONDITIONAL:
                if_true = step.config.get("if_true")
                if_false = step.config.get("if_false")
                
                if if_true:
                    lines.append(f"    {step_id} -->|true| {if_true}")
                if if_false:
                    lines.append(f"    {step_id} -->|false| {if_false}")
                    
        return "\n".join(lines)


class Step:
    """Helper class for creating workflow steps."""
    
    @staticmethod
    def agent(agent_name: str, prompt: str, **kwargs) -> WorkflowStep:
        """Create an agent execution step.
        
        Args:
            agent_name: Name of the agent to run
            prompt: Input prompt for the agent
            **kwargs: Additional configuration
            
        Returns:
            WorkflowStep configured for agent execution
        """
        config = {
            "agent_name": agent_name,
            "prompt": prompt,
            **kwargs
        }
        return WorkflowStep(
            name=f"Run {agent_name}",
            type=StepType.AGENT,
            config=config
        )
    
    @staticmethod
    def parallel(steps: List[WorkflowStep]) -> WorkflowStep:
        """Create a parallel execution step.
        
        Args:
            steps: Steps to run in parallel
            
        Returns:
            WorkflowStep configured for parallel execution
        """
        return WorkflowStep(
            name="Parallel Steps",
            type=StepType.PARALLEL,
            config={"steps": steps}
        )
    
    @staticmethod
    def conditional(
        condition: Callable[[Any], bool],
        if_true: WorkflowStep,
        if_false: WorkflowStep | None = None
    ) -> WorkflowStep:
        """Create a conditional execution step.
        
        Args:
            condition: Function to evaluate condition
            if_true: Step to run if condition is true
            if_false: Step to run if condition is false
            
        Returns:
            WorkflowStep configured for conditional execution
        """
        return WorkflowStep(
            name="Conditional",
            type=StepType.CONDITIONAL,
            config={
                "condition": condition,
                "if_true": if_true.id,
                "if_false": if_false.id if if_false else None
            }
        )
    
    @staticmethod
    def loop(
        over: str | Callable[[Any], List[Any]],
        body: WorkflowStep,
        max_iterations: int | None = None
    ) -> WorkflowStep:
        """Create a loop execution step.
        
        Args:
            over: Data path or function to get items
            body: Step to run for each item
            max_iterations: Maximum iterations
            
        Returns:
            WorkflowStep configured for loop execution
        """
        return WorkflowStep(
            name="Loop",
            type=StepType.LOOP,
            config={
                "over": over,
                "body": body.id,
                "max_iterations": max_iterations
            }
        )
    
    @staticmethod
    def transform(transform: Callable[[Any], Any]) -> WorkflowStep:
        """Create a data transformation step.
        
        Args:
            transform: Transformation function
            
        Returns:
            WorkflowStep configured for transformation
        """
        return WorkflowStep(
            name="Transform",
            type=StepType.TRANSFORM,
            config={"transform": transform}
        )
    
    @staticmethod
    def wait(duration: float) -> WorkflowStep:
        """Create a wait step.
        
        Args:
            duration: Duration to wait in seconds
            
        Returns:
            WorkflowStep configured for waiting
        """
        return WorkflowStep(
            name=f"Wait {duration}s",
            type=StepType.WAIT,
            config={"duration": duration}
        )