"""Base Agent - Unified foundation for all AI agent implementations.

This module provides the single base class for all agent operations,
following DRY principles and ensuring consistent behavior across all agents.
"""

from __future__ import annotations

import os
import asyncio
import logging
from abc import ABC, abstractmethod
from typing import Any, Dict, List, Generic, TypeVar, Optional, Protocol
from pathlib import Path
from datetime import datetime
from dataclasses import field, dataclass

from .model_registry import ModelConfig, registry

logger = logging.getLogger(__name__)


# Type variables for generic context
TContext = TypeVar("TContext")
TResult = TypeVar("TResult")


class AgentContext(Protocol[TContext]):
    """Protocol for agent execution context."""
    
    async def log(self, message: str, level: str = "info") -> None:
        """Log a message."""
        ...
    
    async def progress(self, message: str, percentage: Optional[float] = None) -> None:
        """Report progress."""
        ...


@dataclass
class AgentConfig:
    """Configuration for agent execution."""
    
    model: str = "claude-3-5-sonnet-20241022"
    timeout: int = 300
    max_retries: int = 3
    working_dir: Optional[Path] = None
    environment: Dict[str, str] = field(default_factory=dict)
    stream_output: bool = False
    use_worktree: bool = False
    
    def __post_init__(self) -> None:
        """Resolve model name and validate configuration."""
        self.model = registry.resolve(self.model)
        if self.working_dir and not isinstance(self.working_dir, Path):
            self.working_dir = Path(self.working_dir)


@dataclass
class AgentResult:
    """Result from agent execution."""
    
    success: bool
    output: Optional[str] = None
    error: Optional[str] = None
    duration: Optional[float] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    @property
    def content(self) -> str:
        """Get the primary content (output or error)."""
        return self.output if self.success else (self.error or "Unknown error")


class BaseAgent(ABC, Generic[TContext, TResult]):
    """Base class for all AI agents.
    
    This is the single foundation for all agent implementations,
    ensuring consistent behavior and eliminating code duplication.
    """
    
    def __init__(self, config: Optional[AgentConfig] = None) -> None:
        """Initialize agent with configuration.
        
        Args:
            config: Agent configuration
        """
        self.config = config or AgentConfig()
        self._start_time: Optional[datetime] = None
        self._end_time: Optional[datetime] = None
    
    @property
    @abstractmethod
    def name(self) -> str:
        """Agent name."""
        ...
    
    @property
    @abstractmethod
    def description(self) -> str:
        """Agent description."""
        ...
    
    async def execute(
        self,
        prompt: str,
        context: Optional[TContext] = None,
        **kwargs: Any,
    ) -> AgentResult:
        """Execute agent with prompt.
        
        Args:
            prompt: The prompt or task
            context: Execution context
            **kwargs: Additional parameters
            
        Returns:
            Agent execution result
        """
        self._start_time = datetime.now()
        
        try:
            # Setup environment
            env = self._prepare_environment()
            
            # Log start
            if context and hasattr(context, "log"):
                await context.log(f"Starting {self.name} with model {self.config.model}")
            
            # Execute with retries
            result = await self._execute_with_retries(prompt, context, env, **kwargs)
            
            # Calculate duration
            self._end_time = datetime.now()
            duration = (self._end_time - self._start_time).total_seconds()
            
            return AgentResult(
                success=True,
                output=result,
                duration=duration,
                metadata={"model": self.config.model, "agent": self.name},
            )
            
        except Exception as e:
            self._end_time = datetime.now()
            duration = (self._end_time - self._start_time).total_seconds() if self._start_time else None
            
            logger.error(f"Agent {self.name} failed: {e}")
            
            return AgentResult(
                success=False,
                error=str(e),
                duration=duration,
                metadata={"model": self.config.model, "agent": self.name},
            )
    
    def _prepare_environment(self) -> Dict[str, str]:
        """Prepare environment variables for execution.
        
        Returns:
            Environment variables dictionary
        """
        env = os.environ.copy()
        
        # Add model-specific API key
        model_config = registry.get(self.config.model)
        if model_config and model_config.api_key_env:
            key_var = model_config.api_key_env
            if key_var in os.environ:
                env[key_var] = os.environ[key_var]
        
        # Add Hanzo unified auth
        if "HANZO_API_KEY" in os.environ:
            env["HANZO_API_KEY"] = os.environ["HANZO_API_KEY"]
        
        # Add custom environment
        env.update(self.config.environment)
        
        return env
    
    async def _execute_with_retries(
        self,
        prompt: str,
        context: Optional[TContext],
        env: Dict[str, str],
        **kwargs: Any,
    ) -> str:
        """Execute with retry logic.
        
        Args:
            prompt: The prompt
            context: Execution context
            env: Environment variables
            **kwargs: Additional parameters
            
        Returns:
            Execution output
            
        Raises:
            Exception: If all retries fail
        """
        last_error = None
        
        for attempt in range(self.config.max_retries):
            try:
                # Call the implementation
                result = await self._execute_impl(prompt, context, env, **kwargs)
                return result
                
            except asyncio.TimeoutError:
                last_error = f"Timeout after {self.config.timeout} seconds"
                if context and hasattr(context, "log"):
                    await context.log(f"Attempt {attempt + 1} timed out", "warning")
                    
            except Exception as e:
                last_error = str(e)
                if context and hasattr(context, "log"):
                    await context.log(f"Attempt {attempt + 1} failed: {e}", "warning")
                
                # Don't retry on certain errors
                if "unauthorized" in str(e).lower() or "forbidden" in str(e).lower():
                    raise
            
            # Wait before retry (exponential backoff)
            if attempt < self.config.max_retries - 1:
                await asyncio.sleep(2 ** attempt)
        
        raise Exception(f"All {self.config.max_retries} attempts failed. Last error: {last_error}")
    
    @abstractmethod
    async def _execute_impl(
        self,
        prompt: str,
        context: Optional[TContext],
        env: Dict[str, str],
        **kwargs: Any,
    ) -> str:
        """Implementation-specific execution.
        
        Args:
            prompt: The prompt
            context: Execution context
            env: Environment variables
            **kwargs: Additional parameters
            
        Returns:
            Execution output
        """
        ...


class CLIAgent(BaseAgent[TContext, str]):
    """Base class for CLI-based agents."""
    
    @property
    @abstractmethod
    def cli_command(self) -> str:
        """CLI command to execute."""
        ...
    
    def build_command(self, prompt: str, **kwargs: Any) -> List[str]:
        """Build the CLI command.
        
        Args:
            prompt: The prompt
            **kwargs: Additional parameters
            
        Returns:
            Command arguments list
        """
        command = [self.cli_command]
        
        # Add model if specified
        model_config = registry.get(self.config.model)
        if model_config:
            command.extend(["--model", model_config.full_name])
        
        # Add prompt
        command.append(prompt)
        
        return command
    
    async def _execute_impl(
        self,
        prompt: str,
        context: Optional[TContext],
        env: Dict[str, str],
        **kwargs: Any,
    ) -> str:
        """Execute CLI command.
        
        Args:
            prompt: The prompt
            context: Execution context
            env: Environment variables
            **kwargs: Additional parameters
            
        Returns:
            Command output
        """
        command = self.build_command(prompt, **kwargs)
        
        # Execute command
        process = await asyncio.create_subprocess_exec(
            *command,
            stdin=asyncio.subprocess.PIPE,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
            cwd=str(self.config.working_dir) if self.config.working_dir else None,
            env=env,
        )
        
        # Handle timeout
        try:
            stdout, stderr = await asyncio.wait_for(
                process.communicate(prompt.encode() if len(command) == 1 else None),
                timeout=self.config.timeout,
            )
        except asyncio.TimeoutError:
            process.kill()
            raise asyncio.TimeoutError(f"Command timed out after {self.config.timeout} seconds")
        
        # Check for errors
        if process.returncode != 0:
            error_msg = stderr.decode() if stderr else "Command failed"
            raise Exception(error_msg)
        
        return stdout.decode()


class APIAgent(BaseAgent[TContext, str]):
    """Base class for API-based agents."""
    
    async def _execute_impl(
        self,
        prompt: str,
        context: Optional[TContext],
        env: Dict[str, str],
        **kwargs: Any,
    ) -> str:
        """Execute via API.
        
        Args:
            prompt: The prompt
            context: Execution context
            env: Environment variables
            **kwargs: Additional parameters
            
        Returns:
            API response
        """
        # This would be implemented by specific API agents
        # using the appropriate client library
        raise NotImplementedError("API agents must implement _execute_impl")


class AgentOrchestrator:
    """Orchestrator for managing multiple agents."""
    
    def __init__(self, default_config: Optional[AgentConfig] = None) -> None:
        """Initialize orchestrator.
        
        Args:
            default_config: Default configuration for agents
        """
        self.default_config = default_config or AgentConfig()
        self._agents: Dict[str, BaseAgent] = {}
        self._semaphore: Optional[asyncio.Semaphore] = None
    
    def register(self, agent: BaseAgent) -> None:
        """Register an agent.
        
        Args:
            agent: Agent to register
        """
        self._agents[agent.name] = agent
    
    def get_agent(self, name: str) -> Optional[BaseAgent]:
        """Get agent by name.
        
        Args:
            name: Agent name
            
        Returns:
            Agent instance or None
        """
        return self._agents.get(name)
    
    async def execute_single(
        self,
        agent_name: str,
        prompt: str,
        context: Optional[Any] = None,
        **kwargs: Any,
    ) -> AgentResult:
        """Execute single agent.
        
        Args:
            agent_name: Name of agent to use
            prompt: The prompt
            context: Execution context
            **kwargs: Additional parameters
            
        Returns:
            Execution result
        """
        agent = self.get_agent(agent_name)
        if not agent:
            return AgentResult(
                success=False,
                error=f"Agent '{agent_name}' not found",
            )
        
        return await agent.execute(prompt, context, **kwargs)
    
    async def execute_parallel(
        self,
        tasks: List[Dict[str, Any]],
        max_concurrent: int = 5,
    ) -> List[AgentResult]:
        """Execute multiple agents in parallel.
        
        Args:
            tasks: List of task definitions
            max_concurrent: Maximum concurrent executions
            
        Returns:
            List of results
        """
        self._semaphore = asyncio.Semaphore(max_concurrent)
        
        async def run_with_semaphore(task: Dict[str, Any]) -> AgentResult:
            async with self._semaphore:
                return await self.execute_single(
                    task["agent"],
                    task["prompt"],
                    task.get("context"),
                    **task.get("kwargs", {}),
                )
        
        return await asyncio.gather(
            *[run_with_semaphore(task) for task in tasks],
            return_exceptions=False,
        )
    
    async def execute_consensus(
        self,
        prompt: str,
        agents: List[str],
        threshold: float = 0.66,
    ) -> Dict[str, Any]:
        """Execute consensus operation with multiple agents.
        
        Args:
            prompt: The prompt
            agents: List of agent names
            threshold: Agreement threshold
            
        Returns:
            Consensus results
        """
        # Execute all agents in parallel
        tasks = [{"agent": agent, "prompt": prompt} for agent in agents]
        results = await self.execute_parallel(tasks)
        
        # Analyze consensus
        successful = [r for r in results if r.success]
        agreement = len(successful) / len(results) if results else 0
        
        return {
            "consensus_reached": agreement >= threshold,
            "agreement_score": agreement,
            "individual_results": results,
            "agents_used": agents,
        }
    
    async def execute_chain(
        self,
        initial_prompt: str,
        agents: List[str],
    ) -> List[AgentResult]:
        """Execute agents in a chain, passing output forward.
        
        Args:
            initial_prompt: Initial prompt
            agents: List of agent names
            
        Returns:
            List of results from each step
        """
        results = []
        current_prompt = initial_prompt
        
        for agent_name in agents:
            result = await self.execute_single(agent_name, current_prompt)
            results.append(result)
            
            if result.success and result.output:
                # Use output as input for next agent
                current_prompt = f"Review and improve:\n{result.output}"
            else:
                # Chain broken
                break
        
        return results


__all__ = [
    "AgentContext",
    "AgentConfig",
    "AgentResult",
    "BaseAgent",
    "CLIAgent",
    "APIAgent",
    "AgentOrchestrator",
]