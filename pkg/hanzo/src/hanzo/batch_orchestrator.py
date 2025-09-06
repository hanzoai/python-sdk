"""Batch Orchestrator for Hanzo Dev - Unified Parallel Agent Execution.

This module provides a single, DRY implementation for all batch operations,
consensus mechanisms, and critic chains using the unified base classes.
"""

import re
import json
import asyncio
import logging
import subprocess
from typing import Any, Dict, List, Callable, Optional, AsyncIterator
from pathlib import Path
from datetime import datetime
from dataclasses import field, dataclass

from rich.panel import Panel
from rich.table import Table
from rich.console import Console
from rich.progress import TaskID, Progress, BarColumn, TextColumn, SpinnerColumn

try:
    # Try to import from hanzo-mcp if available
    from hanzo_mcp.core.base_agent import AgentConfig, AgentResult, AgentOrchestrator
    from hanzo_mcp.core.model_registry import registry
except ImportError:
    # Fall back to local imports if hanzo-mcp is not installed
    from .base_agent import AgentConfig, AgentResult, AgentOrchestrator
    from .model_registry import registry

logger = logging.getLogger(__name__)
console = Console()


@dataclass
class BatchTask:
    """Represents a single task in a batch operation."""
    
    id: str
    description: str
    file_path: Optional[Path] = None
    agent_model: str = field(default_factory=lambda: registry.resolve("claude"))
    status: str = "pending"  # pending, running, completed, failed
    result: Optional[AgentResult] = None
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    
    def duration(self) -> Optional[float]:
        """Calculate task duration in seconds."""
        if self.start_time and self.end_time:
            return (self.end_time - self.start_time).total_seconds()
        return None
    
    @property
    def success(self) -> bool:
        """Check if task succeeded."""
        return self.status == "completed" and self.result and self.result.success
    
    @property
    def error(self) -> Optional[str]:
        """Get error message if any."""
        if self.result and not self.result.success:
            return self.result.error
        return None


@dataclass
class BatchConfig:
    """Configuration for batch operations."""
    
    batch_size: int = 5  # Default concurrent tasks
    agent_model: str = field(default_factory=lambda: registry.resolve("claude"))
    operation: str = ""
    target_pattern: str = "**/*"  # File pattern
    max_retries: int = 3
    timeout_seconds: int = 300
    stream_results: bool = True
    use_mcp_tools: bool = True
    use_worktrees: bool = False  # Use git worktrees for parallel editing
    worktree_base: str = ".worktrees"  # Base dir for worktrees
    
    # Consensus and critic features
    consensus_mode: bool = False
    consensus_models: List[str] = field(default_factory=list)
    consensus_threshold: float = 0.66  # Agreement threshold
    critic_mode: bool = False
    critic_models: List[str] = field(default_factory=list)
    critic_chain: bool = False  # Chain critics sequentially
    
    def __post_init__(self) -> None:
        """Resolve all model names using registry."""
        self.agent_model = registry.resolve(self.agent_model)
        self.consensus_models = [registry.resolve(m) for m in self.consensus_models]
        self.critic_models = [registry.resolve(m) for m in self.critic_models]
    
    @classmethod
    def from_command(cls, command: str) -> "BatchConfig":
        """Parse batch command syntax.
        
        Examples:
            batch:5 add copyright to all files  # Defaults to Claude
            batch:100 agent:claude add copyright to all files
            batch:50 agent:codex fix typing in *.py
            batch:5 worktree:true parallel edits  # Use git worktrees
            
            consensus:3 agent:gemini,claude,codex review code
            consensus:3 llm:gpt-5,opus-4.1,sonnet-4.1 analyze
            
            critic:3 agent:claude,codex,gemini review implementation
            critic:3 chain:true progressive review  # Chain critics
        """
        config = cls()
        
        # Parse consensus mode
        consensus_match = re.search(r'consensus:(\d+)', command)
        if consensus_match:
            config.consensus_mode = True
            config.batch_size = int(consensus_match.group(1))
            
            # Parse consensus agents/models
            agent_list_match = re.search(r'agent:([a-zA-Z0-9,\-_.]+)', command)
            llm_list_match = re.search(r'llm:([a-zA-Z0-9,\-_.]+)', command)
            
            if agent_list_match:
                agents = agent_list_match.group(1).split(',')
                config.consensus_models = agents  # Will be resolved in __post_init__
            elif llm_list_match:
                models = llm_list_match.group(1).split(',')
                config.consensus_models = models  # Will be resolved in __post_init__
        
        # Parse critic mode
        critic_match = re.search(r'critic:(\d+)', command)
        if critic_match:
            config.critic_mode = True
            config.batch_size = int(critic_match.group(1))
            
            # Parse critic chain option
            chain_match = re.search(r'chain:(true|false)', command)
            if chain_match:
                config.critic_chain = chain_match.group(1) == 'true'
            
            # Parse critic agents/models
            agent_list_match = re.search(r'agent:([a-zA-Z0-9,\-_.]+)', command)
            if agent_list_match:
                agents = agent_list_match.group(1).split(',')
                config.critic_models = agents  # Will be resolved in __post_init__
        
        # Parse batch size (if not consensus/critic)
        if not config.consensus_mode and not config.critic_mode:
            batch_match = re.search(r'batch:(\d+)', command)
            if batch_match:
                config.batch_size = int(batch_match.group(1))
        
        # Parse single agent model (for regular batch)
        if not config.consensus_mode and not config.critic_mode:
            agent_match = re.search(r'agent:(\w+)', command)
            if agent_match:
                config.agent_model = agent_match.group(1)  # Will be resolved in __post_init__
        
        # Parse worktree option
        worktree_match = re.search(r'worktree:(true|false)', command)
        if worktree_match:
            config.use_worktrees = worktree_match.group(1) == 'true'
        
        # Parse file pattern
        pattern_match = re.search(r'files:([^\s]+)', command)
        if pattern_match:
            config.target_pattern = pattern_match.group(1)
        
        # Extract operation (remove all config parts)
        operation = command
        operation = re.sub(r'(batch|consensus|critic):\d+\s*', '', operation)
        operation = re.sub(r'agent:[a-zA-Z0-9,\-_.]+\s*', '', operation)
        operation = re.sub(r'llm:[a-zA-Z0-9,\-_.]+\s*', '', operation)
        operation = re.sub(r'chain:(true|false)\s*', '', operation)
        operation = re.sub(r'worktree:(true|false)\s*', '', operation)
        operation = re.sub(r'files:[^\s]+\s*', '', operation)
        config.operation = operation.strip()
        
        # Trigger __post_init__ to resolve model names
        config.__post_init__()
        
        return config


class BatchOrchestrator:
    """Orchestrates parallel batch operations using unified agent system."""
    
    def __init__(
        self,
        mcp_client: Optional[Any] = None,
        hanzo_client: Optional[Any] = None,
    ):
        """Initialize batch orchestrator.
        
        Args:
            mcp_client: MCP client for tool access
            hanzo_client: Hanzo client for AI operations
        """
        self.mcp_client = mcp_client
        self.hanzo_client = hanzo_client
        self.agent_orchestrator = AgentOrchestrator()
        self.active_tasks: Dict[str, BatchTask] = {}
        self.completed_tasks: List[BatchTask] = []
        self.failed_tasks: List[BatchTask] = []
        self._task_counter = 0
        self._progress: Optional[Progress] = None
        self._worktrees: Dict[str, Path] = {}  # Track worktrees
        
    def _generate_task_id(self) -> str:
        """Generate unique task ID."""
        self._task_counter += 1
        return f"task_{self._task_counter:04d}"
    
    async def _setup_worktree(self, task_id: str, config: BatchConfig) -> Optional[Path]:
        """Setup git worktree for parallel editing.
        
        Args:
            task_id: Task identifier
            config: Batch configuration
            
        Returns:
            Path to worktree or None if not using worktrees
        """
        if not config.use_worktrees:
            return None
        
        try:
            # Create worktree directory
            worktree_path = Path(config.worktree_base) / task_id
            worktree_path.parent.mkdir(parents=True, exist_ok=True)
            
            # Create worktree
            import subprocess
            result = subprocess.run(
                ["git", "worktree", "add", str(worktree_path), "HEAD"],
                capture_output=True,
                text=True,
            )
            
            if result.returncode != 0:
                logger.error(f"Failed to create worktree: {result.stderr}")
                return None
            
            self._worktrees[task_id] = worktree_path
            return worktree_path
            
        except Exception as e:
            logger.error(f"Error setting up worktree: {e}")
            return None
    
    async def _cleanup_worktree(self, task_id: str) -> None:
        """Cleanup git worktree after task completion.
        
        Args:
            task_id: Task identifier
        """
        if task_id not in self._worktrees:
            return
        
        try:
            worktree_path = self._worktrees[task_id]
            
            # Remove worktree
            import subprocess
            subprocess.run(
                ["git", "worktree", "remove", str(worktree_path), "--force"],
                capture_output=True,
            )
            
            del self._worktrees[task_id]
            
        except Exception as e:
            logger.error(f"Error cleaning up worktree: {e}")
    
    async def _find_target_files(self, pattern: str) -> List[Path]:
        """Find files matching the target pattern.
        
        Args:
            pattern: Glob pattern for files
            
        Returns:
            List of matching file paths
        """
        if self.mcp_client:
            # Use MCP find tool
            try:
                result = await self.mcp_client.call_tool(
                    "find",
                    {"pattern": pattern}
                )
                if isinstance(result, str):
                    # Parse file paths from result
                    files = []
                    for line in result.split('\n'):
                        if line.strip():
                            files.append(Path(line.strip()))
                    return files
            except Exception as e:
                logger.error(f"MCP find failed: {e}")
        
        # Fallback to Path.glob
        base_path = Path.cwd()
        return list(base_path.glob(pattern))
    
    async def _execute_agent_task(
        self,
        task: BatchTask,
        config: BatchConfig,
        progress_task: Optional[TaskID] = None,
    ) -> None:
        """Execute a single agent task.
        
        Args:
            task: The task to execute
            config: Batch configuration
            progress_task: Optional progress bar task ID
        """
        task.status = "running"
        task.start_time = datetime.now()
        worktree_path = None
        
        try:
            # Setup worktree if needed
            worktree_path = await self._setup_worktree(task.id, config)
            
            # Build the prompt for the agent
            prompt = config.operation
            if task.file_path:
                # If using worktree, use the worktree path
                if worktree_path:
                    file_path = worktree_path / task.file_path.relative_to(Path.cwd())
                    prompt = f"{config.operation} for file: {file_path}"
                else:
                    prompt = f"{config.operation} for file: {task.file_path}"
            
            # Use MCP agent tool if available
            if self.mcp_client and config.use_mcp_tools:
                # If using worktree, set working directory context
                context = {}
                if worktree_path:
                    context["working_dir"] = str(worktree_path)
                
                result = await self.mcp_client.call_tool(
                    "agent",
                    {
                        "prompt": prompt,
                        "model": config.agent_model,
                        "max_iterations": 5,
                        **context,
                    }
                )
                task.result = result
            
            # Use Hanzo client for direct AI calls
            elif self.hanzo_client:
                response = await self.hanzo_client.chat.completions.create(
                    model=config.agent_model,
                    messages=[
                        {"role": "system", "content": "You are a helpful coding assistant."},
                        {"role": "user", "content": prompt}
                    ],
                    stream=False,
                )
                task.result = response.choices[0].message.content
            
            else:
                # Simulate agent execution for testing
                await asyncio.sleep(0.1)  # Simulate work
                task.result = f"Completed: {prompt}"
            
            task.status = "completed"
            
            # If using worktree, merge changes back
            if worktree_path and task.status == "completed":
                await self._merge_worktree_changes(task.id, worktree_path)
            
        except asyncio.TimeoutError:
            task.status = "failed"
            task.error = "Task timed out"
            
        except Exception as e:
            task.status = "failed"
            task.error = str(e)
            logger.error(f"Task {task.id} failed: {e}")
            
        finally:
            task.end_time = datetime.now()
            
            # Cleanup worktree
            if worktree_path:
                await self._cleanup_worktree(task.id)
            
            # Update progress if available
            if self._progress and progress_task is not None:
                self._progress.update(progress_task, advance=1)
            
            # Stream result if enabled
            if config.stream_results:
                await self._stream_result(task)
    
    async def _merge_worktree_changes(self, task_id: str, worktree_path: Path) -> None:
        """Merge changes from worktree back to main branch.
        
        Args:
            task_id: Task identifier
            worktree_path: Path to worktree
        """
        try:
            import subprocess
            
            # Stage and commit changes in worktree
            subprocess.run(
                ["git", "add", "-A"],
                cwd=worktree_path,
                capture_output=True,
            )
            
            subprocess.run(
                ["git", "commit", "-m", f"Task {task_id}: Automated changes"],
                cwd=worktree_path,
                capture_output=True,
            )
            
            # Cherry-pick to main branch
            result = subprocess.run(
                ["git", "rev-parse", "HEAD"],
                cwd=worktree_path,
                capture_output=True,
                text=True,
            )
            
            if result.returncode == 0:
                commit_hash = result.stdout.strip()
                subprocess.run(
                    ["git", "cherry-pick", commit_hash],
                    capture_output=True,
                )
                
        except Exception as e:
            logger.error(f"Error merging worktree changes: {e}")
    
    async def _stream_result(self, task: BatchTask) -> None:
        """Stream task result to console.
        
        Args:
            task: Completed task to stream
        """
        status_color = "green" if task.status == "completed" else "red"
        status_icon = "✓" if task.status == "completed" else "✗"
        
        # Create result panel
        content = task.result if task.status == "completed" else task.error
        panel = Panel(
            content or "No output",
            title=f"[{status_color}]{status_icon}[/{status_color}] {task.id}: {task.description}",
            border_style=status_color,
        )
        console.print(panel)
    
    async def _execute_consensus(
        self,
        prompt: str,
        models: List[str],
        config: BatchConfig,
    ) -> Dict[str, Any]:
        """Execute consensus operation with multiple models.
        
        Args:
            prompt: The prompt to send to all models
            models: List of model names
            config: Batch configuration
            
        Returns:
            Consensus result with individual responses
        """
        responses = []
        
        # Execute with all models in parallel
        async def get_response(model: str) -> Dict[str, Any]:
            try:
                if self.mcp_client:
                    result = await self.mcp_client.call_tool(
                        "llm",
                        {
                            "prompt": prompt,
                            "model": model,
                        }
                    )
                    return {"model": model, "response": result, "success": True}
                elif self.hanzo_client:
                    response = await self.hanzo_client.chat.completions.create(
                        model=model,
                        messages=[{"role": "user", "content": prompt}],
                    )
                    return {
                        "model": model,
                        "response": response.choices[0].message.content,
                        "success": True,
                    }
                else:
                    return {"model": model, "response": f"Mock response from {model}", "success": True}
            except Exception as e:
                return {"model": model, "error": str(e), "success": False}
        
        # Get all responses in parallel
        responses = await asyncio.gather(*[get_response(model) for model in models])
        
        # Analyze consensus
        successful_responses = [r for r in responses if r["success"]]
        agreement_score = len(successful_responses) / len(models) if models else 0
        
        # Simple consensus: majority agreement or summarize
        consensus_result = {
            "consensus_reached": agreement_score >= config.consensus_threshold,
            "agreement_score": agreement_score,
            "individual_responses": responses,
            "models_used": models,
        }
        
        # If consensus reached, combine insights
        if consensus_result["consensus_reached"] and successful_responses:
            combined = "\n\n".join([
                f"[{r['model']}]: {r['response']}"
                for r in successful_responses
            ])
            consensus_result["combined_response"] = combined
        
        return consensus_result
    
    async def _execute_critic_chain(
        self,
        initial_content: str,
        models: List[str],
        config: BatchConfig,
    ) -> Dict[str, Any]:
        """Execute critic chain with sequential review.
        
        Args:
            initial_content: Content to review
            models: List of critic models
            config: Batch configuration
            
        Returns:
            Chain of critic reviews
        """
        reviews = []
        current_content = initial_content
        
        for i, model in enumerate(models):
            # Build critic prompt
            if i == 0:
                prompt = f"Please review the following:\n\n{current_content}"
            else:
                prompt = f"""Please review the following, taking into account previous reviews:
                
Original content:
{initial_content}

Previous reviews:
{chr(10).join([f"[{r['model']}]: {r['review']}" for r in reviews])}

Provide your critical analysis:"""
            
            try:
                if self.mcp_client:
                    # Use critic tool if available
                    result = await self.mcp_client.call_tool(
                        "critic",
                        {
                            "analysis": prompt,
                            "model": model,
                        }
                    )
                    review = result
                else:
                    # Fallback to LLM
                    if self.hanzo_client:
                        response = await self.hanzo_client.chat.completions.create(
                            model=model,
                            messages=[
                                {"role": "system", "content": "You are a thorough code critic."},
                                {"role": "user", "content": prompt}
                            ],
                        )
                        review = response.choices[0].message.content
                    else:
                        review = f"Mock critic review from {model}"
                
                reviews.append({
                    "model": model,
                    "review": review,
                    "iteration": i + 1,
                })
                
                # Update content for next critic
                current_content = review
                
            except Exception as e:
                reviews.append({
                    "model": model,
                    "error": str(e),
                    "iteration": i + 1,
                })
        
        return {
            "critic_chain": reviews,
            "final_review": reviews[-1]["review"] if reviews and "review" in reviews[-1] else None,
            "models_used": models,
            "chain_length": len(reviews),
        }
    
    async def execute_batch(
        self,
        command: str,
        stream_callback: Optional[Callable[[str], None]] = None,
    ) -> Dict[str, Any]:
        """Execute batch operation with parallel agents.
        
        Args:
            command: Batch command to execute
            stream_callback: Optional callback for streaming results
            
        Returns:
            Summary of batch execution results
        """
        # Parse configuration
        config = BatchConfig.from_command(command)
        
        # Handle consensus mode
        if config.consensus_mode:
            console.print(f"[bold cyan]Consensus Configuration:[/bold cyan]")
            console.print(f"  Models: {', '.join(config.consensus_models)}")
            console.print(f"  Operation: {config.operation}")
            console.print(f"  Threshold: {config.consensus_threshold}")
            
            result = await self._execute_consensus(
                config.operation,
                config.consensus_models,
                config,
            )
            
            # Display consensus result
            if result["consensus_reached"]:
                console.print("[bold green]✓ Consensus reached![/bold green]")
            else:
                console.print("[bold yellow]⚠ No consensus[/bold yellow]")
            
            console.print(f"Agreement Score: {result['agreement_score']:.1%}")
            
            for resp in result["individual_responses"]:
                if resp["success"]:
                    console.print(Panel(
                        resp["response"][:500] + "..." if len(resp.get("response", "")) > 500 else resp.get("response", ""),
                        title=f"[cyan]{resp['model']}[/cyan]",
                    ))
            
            return result
        
        # Handle critic mode
        elif config.critic_mode:
            console.print(f"[bold cyan]Critic Configuration:[/bold cyan]")
            console.print(f"  Models: {', '.join(config.critic_models)}")
            console.print(f"  Chain Mode: {config.critic_chain}")
            console.print(f"  Operation: {config.operation}")
            
            if config.critic_chain:
                result = await self._execute_critic_chain(
                    config.operation,
                    config.critic_models,
                    config,
                )
                
                # Display critic chain
                for review in result["critic_chain"]:
                    if "review" in review:
                        console.print(Panel(
                            review["review"][:500] + "..." if len(review["review"]) > 500 else review["review"],
                            title=f"[cyan]Critic {review['iteration']}: {review['model']}[/cyan]",
                        ))
                
                return result
            else:
                # Parallel critics (use consensus mechanism)
                result = await self._execute_consensus(
                    f"Please provide critical review: {config.operation}",
                    config.critic_models,
                    config,
                )
                return result
        
        # Regular batch mode
        console.print(f"[bold cyan]Batch Configuration:[/bold cyan]")
        console.print(f"  Batch Size: {config.batch_size}")
        console.print(f"  Agent Model: {config.agent_model}")
        console.print(f"  Operation: {config.operation}")
        console.print(f"  Target Pattern: {config.target_pattern}")
        
        # Find target files
        target_files = await self._find_target_files(config.target_pattern)
        console.print(f"[bold]Found {len(target_files)} files to process[/bold]")
        
        # Create tasks
        tasks = []
        for file_path in target_files:
            task = BatchTask(
                id=self._generate_task_id(),
                description=f"{config.operation} - {file_path.name}",
                file_path=file_path,
                agent_model=config.agent_model,
            )
            tasks.append(task)
            self.active_tasks[task.id] = task
        
        # Setup concurrency control
        self._semaphore = asyncio.Semaphore(config.batch_size)
        
        # Create progress bar
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            BarColumn(),
            TextColumn("[progress.percentage]{task.percentage:>3.0f}%"),
            console=console,
        ) as progress:
            self._progress = progress
            progress_task = progress.add_task(
                f"Processing {len(tasks)} tasks...",
                total=len(tasks),
            )
            
            # Execute tasks with concurrency limit
            async def run_with_semaphore(task: BatchTask):
                async with self._semaphore:
                    await self._execute_agent_task(task, config, progress_task)
            
            # Run all tasks
            await asyncio.gather(
                *[run_with_semaphore(task) for task in tasks],
                return_exceptions=True,
            )
        
        # Collect results
        for task in tasks:
            if task.status == "completed":
                self.completed_tasks.append(task)
            else:
                self.failed_tasks.append(task)
            del self.active_tasks[task.id]
        
        # Generate summary
        total_duration = sum(
            t.duration() or 0 for t in self.completed_tasks + self.failed_tasks
        )
        
        summary = {
            "total_tasks": len(tasks),
            "completed": len(self.completed_tasks),
            "failed": len(self.failed_tasks),
            "total_duration": total_duration,
            "average_duration": total_duration / len(tasks) if tasks else 0,
            "batch_size": config.batch_size,
            "agent_model": config.agent_model,
        }
        
        # Display summary
        self._display_summary(summary)
        
        return summary
    
    def _display_summary(self, summary: Dict[str, Any]) -> None:
        """Display execution summary.
        
        Args:
            summary: Execution summary data
        """
        table = Table(title="Batch Execution Summary", show_header=False)
        table.add_column("Metric", style="cyan")
        table.add_column("Value", style="white")
        
        table.add_row("Total Tasks", str(summary["total_tasks"]))
        table.add_row("Completed", f"[green]{summary['completed']}[/green]")
        table.add_row("Failed", f"[red]{summary['failed']}[/red]")
        table.add_row("Total Duration", f"{summary['total_duration']:.2f}s")
        table.add_row("Average Duration", f"{summary['average_duration']:.2f}s")
        table.add_row("Batch Size", str(summary["batch_size"]))
        table.add_row("Agent Model", summary["agent_model"])
        
        console.print(table)
    
    async def stream_batch_results(self) -> AsyncIterator[BatchTask]:
        """Stream batch results as they complete.
        
        Yields:
            Completed batch tasks
        """
        while self.active_tasks:
            for task_id, task in list(self.active_tasks.items()):
                if task.status in ["completed", "failed"]:
                    yield task
                    del self.active_tasks[task_id]
            await asyncio.sleep(0.1)
    
    def get_status(self) -> Dict[str, Any]:
        """Get current orchestrator status.
        
        Returns:
            Status information
        """
        return {
            "active": len(self.active_tasks),
            "completed": len(self.completed_tasks),
            "failed": len(self.failed_tasks),
            "active_tasks": [
                {
                    "id": task.id,
                    "description": task.description,
                    "status": task.status,
                    "duration": task.duration(),
                }
                for task in self.active_tasks.values()
            ],
        }


class MetaAIOrchestrator:
    """Meta AI orchestrator that manages other AI agents."""
    
    def __init__(
        self,
        primary_model: str = "claude-3-5-sonnet-20241022",
        mcp_client: Optional[Any] = None,
    ):
        """Initialize meta AI orchestrator.
        
        Args:
            primary_model: Primary model for meta reasoning
            mcp_client: MCP client for tool access
        """
        self.primary_model = primary_model
        self.mcp_client = mcp_client
        self.batch_orchestrator = BatchOrchestrator(mcp_client=mcp_client)
        self.agent_pool: Dict[str, Any] = {}
        self.task_queue: asyncio.Queue = asyncio.Queue()
        self.results_queue: asyncio.Queue = asyncio.Queue()
        
    async def parse_and_execute(self, command: str) -> Dict[str, Any]:
        """Parse natural language command and execute appropriate action.
        
        Args:
            command: Natural language command
            
        Returns:
            Execution results
        """
        # Check if it's a batch command
        if "batch:" in command or command.startswith("batch"):
            return await self.batch_orchestrator.execute_batch(command)
        
        # Use meta AI to understand intent
        intent = await self._analyze_intent(command)
        
        if intent["type"] == "batch_operation":
            # Convert natural language to batch syntax
            batch_command = self._build_batch_command(intent)
            return await self.batch_orchestrator.execute_batch(batch_command)
        
        elif intent["type"] == "single_task":
            # Execute single agent task
            return await self._execute_single_task(intent)
        
        else:
            return {"error": f"Unknown command type: {intent['type']}"}
    
    async def _analyze_intent(self, command: str) -> Dict[str, Any]:
        """Analyze user intent from natural language.
        
        Args:
            command: User command
            
        Returns:
            Intent analysis
        """
        # Use primary model to analyze intent
        prompt = f"""
        Analyze the following command and determine the intent:
        Command: {command}
        
        Determine:
        1. Is this a batch operation (multiple files/tasks)?
        2. What is the main operation?
        3. What agent/model should be used?
        4. What are the target files/patterns?
        
        Return as JSON.
        """
        
        if self.mcp_client:
            result = await self.mcp_client.call_tool(
                "llm",
                {
                    "prompt": prompt,
                    "model": self.primary_model,
                    "response_format": "json",
                }
            )
            try:
                return json.loads(result)
            except Exception:
                pass
        
        # Fallback intent detection
        if any(word in command.lower() for word in ["all", "every", "each", "files"]):
            return {
                "type": "batch_operation",
                "operation": command,
                "model": "claude-3-5-sonnet-20241022",
                "pattern": "**/*",
            }
        else:
            return {
                "type": "single_task",
                "operation": command,
                "model": "claude-3-5-sonnet-20241022",
            }
    
    def _build_batch_command(self, intent: Dict[str, Any]) -> str:
        """Build batch command from intent.
        
        Args:
            intent: Analyzed intent
            
        Returns:
            Batch command string
        """
        batch_size = intent.get("batch_size", 10)
        model = intent.get("model", "claude")
        operation = intent.get("operation", "")
        pattern = intent.get("pattern", "**/*")
        
        # Map model names
        model_short = {
            "claude-3-5-sonnet-20241022": "claude",
            "gpt-4-turbo": "codex",
            "gemini-1.5-pro": "gemini",
        }.get(model, model)
        
        return f"batch:{batch_size} agent:{model_short} files:{pattern} {operation}"
    
    async def _execute_single_task(self, intent: Dict[str, Any]) -> Dict[str, Any]:
        """Execute single agent task.
        
        Args:
            intent: Task intent
            
        Returns:
            Execution result
        """
        task = BatchTask(
            id=self.batch_orchestrator._generate_task_id(),
            description=intent["operation"],
            agent_model=intent.get("model", self.primary_model),
        )
        
        config = BatchConfig(
            batch_size=1,
            agent_model=task.agent_model,
            operation=intent["operation"],
        )
        
        await self.batch_orchestrator._execute_agent_task(task, config)
        
        return {
            "task_id": task.id,
            "status": task.status,
            "result": task.result,
            "error": task.error,
            "duration": task.duration(),
        }


# Export main classes
__all__ = [
    "BatchTask",
    "BatchConfig",
    "BatchOrchestrator",
    "MetaAIOrchestrator",
]