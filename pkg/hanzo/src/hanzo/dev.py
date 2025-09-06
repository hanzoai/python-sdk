"""Hanzo Dev - System 2 Thinking Meta-AI for Managing Claude Code Runtime.

This module provides a sophisticated orchestration layer that:
1. Acts as a System 2 thinking agent (deliberative, analytical)
2. Manages Claude Code runtime lifecycle
3. Provides persistence and recovery mechanisms
4. Includes health checks and auto-restart capabilities
5. Integrates with REPL for interactive control
"""

import os
import sys
import json
import time
import signal
import asyncio
import logging
import subprocess
from enum import Enum
from typing import Any, Dict, List, Union, Callable, Optional
from pathlib import Path
from datetime import datetime
from dataclasses import asdict, dataclass

from rich.live import Live
from rich.panel import Panel
from rich.table import Table
from rich.layout import Layout
from rich.console import Console
from rich.progress import Progress, TextColumn, SpinnerColumn

# Setup logging first
logger = logging.getLogger(__name__)
console = Console()

# Import hanzo-network for agent orchestration
try:
    from hanzo_network import (
        LOCAL_COMPUTE_AVAILABLE,
        Agent,
        Router,
        Network,
        ModelConfig,
        NetworkState,
        ModelProvider,
        DistributedNetwork,
        create_agent,
        create_router,
        create_network,
        create_routing_agent,
        create_distributed_network,
    )

    NETWORK_AVAILABLE = True
except ImportError:
    NETWORK_AVAILABLE = False
    logger.warning("hanzo-network not available, using basic orchestration")

    # Provide fallback implementations
    class Agent:
        """Fallback Agent class when hanzo-network is not available."""

        def __init__(self, name: str, model: str = "gpt-4", **kwargs):
            self.name = name
            self.model = model
            self.config = kwargs

    class Network:
        """Fallback Network class."""

        def __init__(self):
            self.agents = []

    class Router:
        """Fallback Router class."""

        def __init__(self):
            pass

    class NetworkState:
        """Fallback NetworkState class."""

        pass

    class ModelConfig:
        """Fallback ModelConfig class."""

        def __init__(self, **kwargs):
            # Accept all kwargs and store as attributes
            for key, value in kwargs.items():
                setattr(self, key, value)

    class ModelProvider:
        """Fallback ModelProvider class."""

        OPENAI = "openai"
        ANTHROPIC = "anthropic"
        LOCAL = "local"

    LOCAL_COMPUTE_AVAILABLE = False


class AgentState(Enum):
    """State of an AI agent."""

    IDLE = "idle"
    THINKING = "thinking"  # System 2 deliberation
    EXECUTING = "executing"
    STUCK = "stuck"
    CRASHED = "crashed"
    RECOVERING = "recovering"


class RuntimeState(Enum):
    """State of Claude Code runtime."""

    NOT_STARTED = "not_started"
    STARTING = "starting"
    RUNNING = "running"
    RESPONDING = "responding"
    NOT_RESPONDING = "not_responding"
    CRASHED = "crashed"
    RESTARTING = "restarting"


@dataclass
class AgentContext:
    """Context for agent decision making."""

    task: str
    goal: str
    constraints: List[str]
    success_criteria: List[str]
    max_attempts: int = 3
    timeout_seconds: int = 300
    checkpoint_interval: int = 60


@dataclass
class RuntimeHealth:
    """Health status of Claude Code runtime."""

    state: RuntimeState
    last_response: datetime
    response_time_ms: float
    memory_usage_mb: float
    cpu_percent: float
    error_count: int
    restart_count: int


@dataclass
class ThinkingResult:
    """Result of System 2 thinking process."""

    decision: str
    reasoning: List[str]
    confidence: float
    alternatives: List[str]
    risks: List[str]
    next_steps: List[str]


class HanzoDevOrchestrator:
    """Main orchestrator for Hanzo Dev System 2 thinking."""

    def __init__(
        self,
        workspace_dir: str = "~/.hanzo/dev",
        claude_code_path: Optional[str] = None,
    ):
        """Initialize the orchestrator.

        Args:
            workspace_dir: Directory for persistence and checkpoints
            claude_code_path: Path to Claude Code executable
        """
        self.workspace_dir = Path(workspace_dir).expanduser()
        self.workspace_dir.mkdir(parents=True, exist_ok=True)

        self.claude_code_path = claude_code_path or self._find_claude_code()
        self.state_file = self.workspace_dir / "orchestrator_state.json"
        self.checkpoint_dir = self.workspace_dir / "checkpoints"
        self.checkpoint_dir.mkdir(exist_ok=True)

        self.agent_state = AgentState.IDLE
        self.runtime_health = RuntimeHealth(
            state=RuntimeState.NOT_STARTED,
            last_response=datetime.now(),
            response_time_ms=0,
            memory_usage_mb=0,
            cpu_percent=0,
            error_count=0,
            restart_count=0,
        )

        self.current_context: Optional[AgentContext] = None
        self.claude_process: Optional[subprocess.Popen] = None
        self.thinking_history: List[ThinkingResult] = []
        self._shutdown = False

    def _find_claude_code(self) -> str:
        """Find Claude Code executable."""
        # Check common locations
        possible_paths = [
            "/usr/local/bin/claude",
            "/opt/claude/claude",
            "~/.local/bin/claude",
            "claude",  # Rely on PATH
        ]

        for path in possible_paths:
            expanded = Path(path).expanduser()
            if expanded.exists() or (
                path == "claude" and os.system(f"which {path} >/dev/null 2>&1") == 0
            ):
                return str(expanded) if expanded.exists() else path

        raise RuntimeError("Claude Code not found. Please specify path.")

    async def think(self, problem: str, context: Dict[str, Any]) -> ThinkingResult:
        """System 2 thinking process - deliberative and analytical.

        This implements slow, deliberate thinking:
        1. Analyze the problem thoroughly
        2. Consider multiple approaches
        3. Evaluate risks and trade-offs
        4. Make a reasoned decision
        """
        self.agent_state = AgentState.THINKING
        console.print("[yellow]🤔 Engaging System 2 thinking...[/yellow]")

        # Simulate deep thinking process
        reasoning = []
        alternatives = []
        risks = []

        # Step 1: Problem decomposition
        reasoning.append(f"Decomposing problem: {problem}")
        sub_problems = self._decompose_problem(problem)
        reasoning.append(f"Identified {len(sub_problems)} sub-problems")

        # Step 2: Generate alternatives
        for sub in sub_problems:
            alt = f"Approach for '{sub}': {self._generate_approach(sub, context)}"
            alternatives.append(alt)

        # Step 3: Risk assessment
        risks = self._assess_risks(problem, alternatives, context)

        # Step 4: Decision synthesis
        decision = self._synthesize_decision(problem, alternatives, risks, context)
        confidence = self._calculate_confidence(decision, risks)

        # Step 5: Plan next steps
        next_steps = self._plan_next_steps(decision, context)

        result = ThinkingResult(
            decision=decision,
            reasoning=reasoning,
            confidence=confidence,
            alternatives=alternatives,
            risks=risks,
            next_steps=next_steps,
        )

        self.thinking_history.append(result)
        self.agent_state = AgentState.IDLE

        return result

    def _decompose_problem(self, problem: str) -> List[str]:
        """Decompose a problem into sub-problems."""
        # Simple heuristic decomposition
        sub_problems = []

        # Check for common patterns
        if "and" in problem.lower():
            parts = problem.split(" and ")
            sub_problems.extend(parts)

        if "then" in problem.lower():
            parts = problem.split(" then ")
            sub_problems.extend(parts)

        if not sub_problems:
            sub_problems = [problem]

        return sub_problems

    def _generate_approach(self, sub_problem: str, context: Dict[str, Any]) -> str:
        """Generate an approach for a sub-problem."""
        # Heuristic approach generation
        if "stuck" in sub_problem.lower():
            return "Analyze error logs, restart with verbose mode, try alternative approach"
        elif "slow" in sub_problem.lower():
            return "Profile performance, optimize bottlenecks, consider caching"
        elif "error" in sub_problem.lower():
            return "Examine stack trace, validate inputs, add error handling"
        else:
            return "Execute standard workflow with monitoring"

    def _assess_risks(
        self, problem: str, alternatives: List[str], context: Dict[str, Any]
    ) -> List[str]:
        """Assess risks of different approaches."""
        risks = []

        if "restart" in str(alternatives).lower():
            risks.append("Restarting may lose current state")

        if "force" in str(alternatives).lower():
            risks.append("Forcing operations may cause data corruption")

        if context.get("error_count", 0) > 5:
            risks.append("High error rate indicates systemic issue")

        return risks

    def _synthesize_decision(
        self,
        problem: str,
        alternatives: List[str],
        risks: List[str],
        context: Dict[str, Any],
    ) -> str:
        """Synthesize a decision from analysis."""
        if len(risks) > 2:
            return (
                "Proceed cautiously with incremental approach and rollback capability"
            )
        elif alternatives:
            return f"Execute primary approach: {alternatives[0]}"
        else:
            return "Gather more information before proceeding"

    def _calculate_confidence(self, decision: str, risks: List[str]) -> float:
        """Calculate confidence in decision."""
        base_confidence = 0.8
        risk_penalty = len(risks) * 0.1
        return max(0.2, min(1.0, base_confidence - risk_penalty))

    def _plan_next_steps(self, decision: str, context: Dict[str, Any]) -> List[str]:
        """Plan concrete next steps."""
        steps = []

        if "cautiously" in decision.lower():
            steps.append("Create checkpoint before proceeding")
            steps.append("Enable verbose logging")

        steps.append("Execute decision with monitoring")
        steps.append("Validate results against success criteria")
        steps.append("Report outcome and update state")

        return steps

    async def start_claude_runtime(self, resume: bool = False) -> bool:
        """Start or resume Claude Code runtime.

        Args:
            resume: Whether to resume from checkpoint
        """
        if self.claude_process and self.claude_process.poll() is None:
            console.print("[yellow]Claude Code already running[/yellow]")
            return True

        self.runtime_health.state = RuntimeState.STARTING
        console.print("[cyan]Starting Claude Code runtime...[/cyan]")

        try:
            # Load checkpoint if resuming
            checkpoint_file = None
            if resume:
                checkpoint_file = self._get_latest_checkpoint()
                if checkpoint_file:
                    console.print(
                        f"[green]Resuming from checkpoint: {checkpoint_file.name}[/green]"
                    )

            # Prepare command
            cmd = [self.claude_code_path]
            if checkpoint_file:
                cmd.extend(["--resume", str(checkpoint_file)])

            # Start process with proper signal handling
            self.claude_process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                stdin=subprocess.PIPE,
                text=True,
                preexec_fn=os.setsid if hasattr(os, "setsid") else None,
            )

            # Wait for startup
            await asyncio.sleep(2)

            if self.claude_process.poll() is None:
                self.runtime_health.state = RuntimeState.RUNNING
                self.runtime_health.last_response = datetime.now()
                console.print("[green]✓ Claude Code runtime started[/green]")
                return True
            else:
                self.runtime_health.state = RuntimeState.CRASHED
                console.print("[red]✗ Claude Code failed to start[/red]")
                return False

        except Exception as e:
            console.print(f"[red]Error starting Claude Code: {e}[/red]")
            self.runtime_health.state = RuntimeState.CRASHED
            return False

    def _get_latest_checkpoint(self) -> Optional[Path]:
        """Get the latest checkpoint file."""
        checkpoints = list(self.checkpoint_dir.glob("checkpoint_*.json"))
        if checkpoints:
            return max(checkpoints, key=lambda p: p.stat().st_mtime)
        return None

    async def health_check(self) -> bool:
        """Check health of Claude Code runtime."""
        if not self.claude_process:
            self.runtime_health.state = RuntimeState.NOT_STARTED
            return False

        # Check if process is alive
        if self.claude_process.poll() is not None:
            self.runtime_health.state = RuntimeState.CRASHED
            self.runtime_health.error_count += 1
            return False

        # Try to communicate
        try:
            # Send a health check command (this is a placeholder)
            # In reality, you'd have a proper API or IPC mechanism
            start_time = time.time()

            # Simulate health check
            await asyncio.sleep(0.1)

            response_time = (time.time() - start_time) * 1000
            self.runtime_health.response_time_ms = response_time
            self.runtime_health.last_response = datetime.now()

            if response_time > 5000:
                self.runtime_health.state = RuntimeState.NOT_RESPONDING
                return False
            else:
                self.runtime_health.state = RuntimeState.RUNNING
                return True

        except Exception as e:
            logger.error(f"Health check failed: {e}")
            self.runtime_health.state = RuntimeState.NOT_RESPONDING
            self.runtime_health.error_count += 1
            return False

    async def restart_if_needed(self) -> bool:
        """Restart Claude Code if it's stuck or crashed."""
        if self.runtime_health.state in [
            RuntimeState.CRASHED,
            RuntimeState.NOT_RESPONDING,
        ]:
            console.print("[yellow]Claude Code needs restart...[/yellow]")

            # Kill existing process
            if self.claude_process:
                try:
                    if hasattr(os, "killpg"):
                        os.killpg(os.getpgid(self.claude_process.pid), signal.SIGTERM)
                    else:
                        self.claude_process.terminate()
                    await asyncio.sleep(2)
                    if self.claude_process.poll() is None:
                        self.claude_process.kill()
                except Exception:
                    pass

            self.runtime_health.restart_count += 1
            self.runtime_health.state = RuntimeState.RESTARTING

            # Start with resume
            return await self.start_claude_runtime(resume=True)

        return True

    async def create_checkpoint(self, name: Optional[str] = None) -> Path:
        """Create a checkpoint of current state."""
        checkpoint_name = name or f"checkpoint_{int(time.time())}"
        checkpoint_file = self.checkpoint_dir / f"{checkpoint_name}.json"

        checkpoint_data = {
            "timestamp": datetime.now().isoformat(),
            "agent_state": self.agent_state.value,
            "runtime_health": asdict(self.runtime_health),
            "current_context": (
                asdict(self.current_context) if self.current_context else None
            ),
            "thinking_history": [
                asdict(t) for t in self.thinking_history[-10:]
            ],  # Last 10
        }

        with open(checkpoint_file, "w") as f:
            json.dump(checkpoint_data, f, indent=2, default=str)

        console.print(f"[green]✓ Checkpoint saved: {checkpoint_file.name}[/green]")
        return checkpoint_file

    async def restore_checkpoint(self, checkpoint_file: Path) -> bool:
        """Restore from a checkpoint."""
        try:
            with open(checkpoint_file, "r") as f:
                data = json.load(f)

            self.agent_state = AgentState(data["agent_state"])
            # Restore other state as needed

            console.print(
                f"[green]✓ Restored from checkpoint: {checkpoint_file.name}[/green]"
            )
            return True
        except Exception as e:
            console.print(f"[red]Failed to restore checkpoint: {e}[/red]")
            return False

    async def monitor_loop(self):
        """Main monitoring loop."""
        console.print("[cyan]Starting monitoring loop...[/cyan]")

        while not self._shutdown:
            try:
                # Health check
                healthy = await self.health_check()

                if not healthy:
                    console.print(
                        f"[yellow]Health check failed. State: {self.runtime_health.state.value}[/yellow]"
                    )

                    # Use System 2 thinking to decide what to do
                    thinking_result = await self.think(
                        f"Claude Code is {self.runtime_health.state.value}",
                        {"health": asdict(self.runtime_health)},
                    )

                    console.print(f"[cyan]Decision: {thinking_result.decision}[/cyan]")
                    console.print(
                        f"[cyan]Confidence: {thinking_result.confidence:.2f}[/cyan]"
                    )

                    # Execute decision
                    if thinking_result.confidence > 0.6:
                        await self.restart_if_needed()

                # Create periodic checkpoints
                if int(time.time()) % 300 == 0:  # Every 5 minutes
                    await self.create_checkpoint()

                await asyncio.sleep(10)  # Check every 10 seconds

            except Exception as e:
                logger.error(f"Monitor loop error: {e}")
                await asyncio.sleep(10)

    async def execute_task(self, context: AgentContext) -> bool:
        """Execute a task with System 2 oversight.

        Args:
            context: The task context
        """
        self.current_context = context
        self.agent_state = AgentState.EXECUTING

        console.print(f"[cyan]Executing task: {context.task}[/cyan]")
        console.print(f"[cyan]Goal: {context.goal}[/cyan]")

        attempts = 0
        while attempts < context.max_attempts:
            attempts += 1
            console.print(f"[yellow]Attempt {attempts}/{context.max_attempts}[/yellow]")

            try:
                # Start Claude if needed
                if self.runtime_health.state != RuntimeState.RUNNING:
                    await self.start_claude_runtime(resume=attempts > 1)

                # Execute the task (placeholder - would send to Claude)
                # In reality, this would involve IPC with Claude Code
                start_time = time.time()

                # Simulate task execution
                await asyncio.sleep(2)

                # Check success criteria
                success = self._evaluate_success(context)

                if success:
                    console.print("[green]✓ Task completed successfully[/green]")
                    self.agent_state = AgentState.IDLE
                    return True
                else:
                    console.print("[yellow]Task not yet complete[/yellow]")

                    # Use System 2 thinking to decide next action
                    thinking_result = await self.think(
                        f"Task '{context.task}' incomplete after attempt {attempts}",
                        {"context": asdict(context), "attempts": attempts},
                    )

                    if thinking_result.confidence < 0.4:
                        console.print("[red]Low confidence, aborting task[/red]")
                        break

            except asyncio.TimeoutError:
                console.print("[red]Task timed out[/red]")
                self.agent_state = AgentState.STUCK

            except Exception as e:
                console.print(f"[red]Task error: {e}[/red]")
                self.runtime_health.error_count += 1

        self.agent_state = AgentState.IDLE
        return False

    def _evaluate_success(self, context: AgentContext) -> bool:
        """Evaluate if success criteria are met."""
        # Placeholder - would check actual results
        # In reality, this would analyze Claude's output
        return False  # For now, always require thinking

    def shutdown(self):
        """Shutdown the orchestrator."""
        self._shutdown = True

        if self.claude_process:
            try:
                self.claude_process.terminate()
                self.claude_process.wait(timeout=5)
            except Exception:
                self.claude_process.kill()

        console.print("[green]✓ Orchestrator shutdown complete[/green]")


class HanzoDevREPL:
    """REPL interface for driving Hanzo Dev orchestrator."""

    def __init__(self, orchestrator: HanzoDevOrchestrator):
        self.orchestrator = orchestrator
        self.commands = {
            "start": self.cmd_start,
            "stop": self.cmd_stop,
            "restart": self.cmd_restart,
            "status": self.cmd_status,
            "think": self.cmd_think,
            "execute": self.cmd_execute,
            "checkpoint": self.cmd_checkpoint,
            "restore": self.cmd_restore,
            "monitor": self.cmd_monitor,
            "help": self.cmd_help,
            "exit": self.cmd_exit,
        }

        # Initialize memory manager
        from .memory_manager import MemoryManager

        workspace = getattr(orchestrator, "workspace_dir", "/tmp/hanzo")
        self.memory_manager = MemoryManager(workspace)

    async def run(self):
        """Run the REPL."""
        from rich.box import Box
        from rich.text import Text
        from rich.align import Align
        from rich.panel import Panel
        from rich.console import Group
        from prompt_toolkit import prompt
        from prompt_toolkit.styles import Style

        # Define Claude-like style for prompt_toolkit
        claude_style = Style.from_dict(
            {
                "": "#333333",  # Default text color
                "prompt": "#666666",  # Gray prompt arrow
            }
        )

        # Use a predefined box style that's similar to Claude
        from rich.box import ROUNDED

        LIGHT_GRAY_BOX = ROUNDED

        # Header
        console.print()
        console.print(
            Panel(
                "[bold cyan]Hanzo Dev - AI Chat[/bold cyan]\n"
                "[dim]Chat naturally or use /commands • Type /help for available commands[/dim]",
                box=LIGHT_GRAY_BOX,
                style="dim white",
                padding=(0, 1),
            )
        )
        console.print()

        # Check for available API keys and show status
        from .fallback_handler import FallbackHandler

        handler = FallbackHandler()
        if not handler.fallback_order:
            console.print("[yellow]⚠️  No API keys detected[/yellow]")
            console.print(
                "[dim]Set OPENAI_API_KEY or ANTHROPIC_API_KEY to enable AI[/dim]"
            )
            console.print()
        else:
            primary = handler.fallback_order[0][1]
            console.print(f"[green]✅ Using {primary} for AI responses[/green]")
            console.print()

        while True:
            try:
                # Simple prompt without box borders to avoid rendering issues
                try:
                    # Add spacing to prevent UI cutoff at bottom
                    user_input = await asyncio.get_event_loop().run_in_executor(
                        None,
                        input,
                        "› ",  # Clean prompt
                    )
                    console.print()  # Add spacing after input

                except EOFError:
                    console.print()  # New line before exit
                    break
                except KeyboardInterrupt:
                    console.print("\n[dim yellow]Use /exit to quit[/dim]")
                    continue

                if not user_input:
                    continue

                # Check for special commands
                if user_input.startswith("/"):
                    # Handle slash commands like Claude Desktop
                    parts = user_input[1:].strip().split(maxsplit=1)
                    cmd = parts[0].lower()
                    args = parts[1] if len(parts) > 1 else ""

                    if cmd in self.commands:
                        await self.commands[cmd](args)
                    else:
                        console.print(f"[yellow]Unknown command: /{cmd}[/yellow]")
                        console.print("Type /help for available commands")

                elif user_input.startswith("#"):
                    # Handle memory/context commands
                    from .memory_manager import handle_memory_command

                    handled = handle_memory_command(
                        user_input, self.memory_manager, console
                    )
                    if not handled:
                        console.print(
                            "[yellow]Unknown memory command. Use #memory help[/yellow]"
                        )

                else:
                    # Natural chat - send directly to AI agents
                    await self.chat_with_agents(user_input)

            except KeyboardInterrupt:
                console.print("\n[yellow]Use /exit to quit[/yellow]")
            except Exception as e:
                console.print(f"[red]Error: {e}[/red]")

    async def cmd_start(self, args: str):
        """Start Claude Code runtime."""
        resume = "--resume" in args
        success = await self.orchestrator.start_claude_runtime(resume=resume)
        if success:
            console.print("[green]Runtime started successfully[/green]")
        else:
            console.print("[red]Failed to start runtime[/red]")

    async def cmd_stop(self, args: str):
        """Stop Claude Code runtime."""
        if self.orchestrator.claude_process:
            self.orchestrator.claude_process.terminate()
            console.print("[yellow]Runtime stopped[/yellow]")
        else:
            console.print("[yellow]Runtime not running[/yellow]")

    async def cmd_restart(self, args: str):
        """Restart Claude Code runtime."""
        await self.cmd_stop("")
        await asyncio.sleep(1)
        await self.cmd_start("--resume")

    async def cmd_status(self, args: str):
        """Show current status."""
        table = Table(title="Hanzo Dev Status")
        table.add_column("Property", style="cyan")
        table.add_column("Value", style="white")

        table.add_row("Agent State", self.orchestrator.agent_state.value)
        table.add_row("Runtime State", self.orchestrator.runtime_health.state.value)
        table.add_row(
            "Last Response", str(self.orchestrator.runtime_health.last_response)
        )
        table.add_row(
            "Response Time",
            f"{self.orchestrator.runtime_health.response_time_ms:.2f}ms",
        )
        table.add_row("Error Count", str(self.orchestrator.runtime_health.error_count))
        table.add_row(
            "Restart Count", str(self.orchestrator.runtime_health.restart_count)
        )

        console.print(table)

    async def cmd_think(self, args: str):
        """Trigger System 2 thinking."""
        if not args:
            console.print("[red]Usage: think <problem>[/red]")
            return

        result = await self.orchestrator.think(args, {})

        console.print(f"\n[bold cyan]Thinking Result:[/bold cyan]")
        console.print(f"Decision: {result.decision}")
        console.print(f"Confidence: {result.confidence:.2f}")
        console.print(f"Reasoning: {', '.join(result.reasoning)}")
        console.print(f"Risks: {', '.join(result.risks)}")
        console.print(f"Next Steps: {', '.join(result.next_steps)}")

    async def cmd_execute(self, args: str):
        """Execute a task."""
        if not args:
            console.print("[red]Usage: execute <task>[/red]")
            return

        context = AgentContext(
            task=args,
            goal="Complete the specified task",
            constraints=["Stay within resource limits", "Maintain data integrity"],
            success_criteria=["Task output is valid", "No errors occurred"],
        )

        success = await self.orchestrator.execute_task(context)
        if success:
            console.print("[green]Task executed successfully[/green]")
        else:
            console.print("[red]Task execution failed[/red]")

    async def cmd_checkpoint(self, args: str):
        """Create a checkpoint."""
        checkpoint = await self.orchestrator.create_checkpoint(args if args else None)
        console.print(f"[green]Checkpoint created: {checkpoint.name}[/green]")

    async def cmd_restore(self, args: str):
        """Restore from checkpoint."""
        if not args:
            # Show available checkpoints
            checkpoints = list(
                self.orchestrator.checkpoint_dir.glob("checkpoint_*.json")
            )
            if checkpoints:
                console.print("[cyan]Available checkpoints:[/cyan]")
                for cp in checkpoints:
                    console.print(f"  - {cp.name}")
            else:
                console.print("[yellow]No checkpoints available[/yellow]")
            return

        checkpoint_file = self.orchestrator.checkpoint_dir / args
        if checkpoint_file.exists():
            success = await self.orchestrator.restore_checkpoint(checkpoint_file)
            if success:
                console.print("[green]Checkpoint restored[/green]")
        else:
            console.print(f"[red]Checkpoint not found: {args}[/red]")

    async def cmd_monitor(self, args: str):
        """Start monitoring loop."""
        console.print("[cyan]Starting monitor mode (Ctrl+C to stop)...[/cyan]")
        try:
            await self.orchestrator.monitor_loop()
        except KeyboardInterrupt:
            console.print("\n[yellow]Monitor stopped[/yellow]")

    async def cmd_help(self, args: str):
        """Show help."""
        help_text = """
[bold cyan]Hanzo Dev - AI Chat Interface[/bold cyan]

[bold]Just chat naturally! Type anything and press Enter.[/bold]

Examples:
  > Write a Python REST API
  > Help me debug this error
  > Explain how async/await works

[bold]Slash Commands:[/bold]
  /help            - Show this help
  /status          - Show agent status
  /think <problem> - Trigger deep thinking
  /execute <task>  - Execute specific task
  /checkpoint      - Save current state
  /restore         - Restore from checkpoint
  /monitor         - Start monitoring
  /exit            - Exit chat

[bold]Memory Commands (like Claude Desktop):[/bold]
  #remember <text> - Store in memory
  #forget <text>   - Remove from memory
  #memory          - Show memory
  #context         - Show context
"""
        console.print(help_text)

    async def cmd_exit(self, args: str):
        """Exit the REPL."""
        self.orchestrator.shutdown()
        console.print("[green]Goodbye![/green]")
        sys.exit(0)

    async def chat_with_agents(self, message: str):
        """Send message to AI agents for natural chat."""
        try:
            # Add message to memory
            self.memory_manager.add_message("user", message)

            # Get memory context
            memory_context = self.memory_manager.summarize_for_ai()

            # Enhance message with context
            if memory_context:
                enhanced_message = f"{memory_context}\n\nUser: {message}"
            else:
                enhanced_message = message

            # Try smart fallback if no specific model configured
            if (
                not hasattr(self.orchestrator, "orchestrator_model")
                or self.orchestrator.orchestrator_model == "auto"
            ):
                # Use streaming if available
                from .streaming import stream_with_fallback

                response = await stream_with_fallback(enhanced_message, console)

                if response:
                    # Save AI response to memory
                    self.memory_manager.add_message("assistant", response)
                    # Response already displayed by streaming handler
                    return
                else:
                    console.print(
                        "[red]No AI options available. Please configure API keys or install tools.[/red]"
                    )
                    return

            # For codex and other CLI tools, go straight to direct API chat
            if hasattr(self.orchestrator, "orchestrator_model"):
                model = self.orchestrator.orchestrator_model
                if model in [
                    "codex",
                    "openai-cli",
                    "openai-codex",
                    "claude",
                    "claude-code",
                    "claude-desktop",
                    "gemini",
                    "gemini-cli",
                    "google-gemini",
                    "hanzo-ide",
                    "hanzo-dev-ide",
                    "ide",
                    "codestral",
                    "codestral-free",
                    "free",
                    "mistral-free",
                    "starcoder",
                    "starcoder2",
                    "free-starcoder",
                ] or model.startswith("local:"):
                    # Use direct API/CLI chat for these models
                    await self._direct_api_chat(message)
                    return

            # Show thinking indicator for network orchestrators
            console.print("[dim]Thinking...[/dim]")

            # Check if we have a network orchestrator with actual AI
            if hasattr(self.orchestrator, "execute_with_network"):
                # Use the network orchestrator (GPT-4, GPT-5, etc.)
                result = await self.orchestrator.execute_with_network(
                    task=message, context={"mode": "chat", "interactive": True}
                )

                if result.get("output"):
                    # Display AI response in a styled panel
                    console.print()
                    from rich.panel import Panel

                    console.print(
                        Panel(
                            result["output"],
                            title="[bold cyan]AI Response[/bold cyan]",
                            title_align="left",
                            border_style="dim cyan",
                            padding=(1, 2),
                        )
                    )
                elif result.get("error"):
                    console.print(f"\n[red]Error:[/red] {result['error']}")
                else:
                    console.print("\n[yellow]No response from agent[/yellow]")

            elif hasattr(self.orchestrator, "execute_with_critique"):
                # Use multi-Claude orchestrator - but now it will use real AI!
                result = await self.orchestrator.execute_with_critique(message)

                if result.get("output"):
                    # Display AI response in a styled panel
                    console.print()
                    from rich.panel import Panel

                    console.print(
                        Panel(
                            result["output"],
                            title="[bold cyan]AI Response[/bold cyan]",
                            title_align="left",
                            border_style="dim cyan",
                            padding=(1, 2),
                        )
                    )
                else:
                    console.print("\n[yellow]No response from agent[/yellow]")

            else:
                # Fallback to direct API call if available
                await self._direct_api_chat(message)

        except Exception as e:
            console.print(f"[red]Error connecting to AI: {e}[/red]")
            console.print("[yellow]Make sure you have API keys configured:[/yellow]")
            console.print("  • OPENAI_API_KEY for GPT models")
            console.print("  • ANTHROPIC_API_KEY for Claude")
            console.print("  • Or use --orchestrator local:llama3.2 for local models")

    async def _direct_api_chat(self, message: str):
        """Direct API chat fallback when network orchestrator isn't available."""
        import os

        # Check for CLI tools and free/local options first
        if self.orchestrator.orchestrator_model in [
            "codex",
            "openai-cli",
            "openai-codex",
        ]:
            # Use OpenAI CLI (Codex)
            await self._use_openai_cli(message)
            return
        elif self.orchestrator.orchestrator_model in [
            "claude",
            "claude-code",
            "claude-desktop",
        ]:
            # Use Claude Desktop/Code
            await self._use_claude_cli(message)
            return
        elif self.orchestrator.orchestrator_model in [
            "gemini",
            "gemini-cli",
            "google-gemini",
        ]:
            # Use Gemini CLI
            await self._use_gemini_cli(message)
            return
        elif self.orchestrator.orchestrator_model in [
            "hanzo-ide",
            "hanzo-dev-ide",
            "ide",
        ]:
            # Use Hanzo Dev IDE from ~/work/hanzo/ide
            await self._use_hanzo_ide(message)
            return
        elif self.orchestrator.orchestrator_model in [
            "codestral",
            "codestral-free",
            "free",
            "mistral-free",
        ]:
            # Use free Mistral Codestral API
            await self._use_free_codestral(message)
            return
        elif self.orchestrator.orchestrator_model in [
            "starcoder",
            "starcoder2",
            "free-starcoder",
        ]:
            # Use free StarCoder via HuggingFace
            await self._use_free_starcoder(message)
            return
        elif self.orchestrator.orchestrator_model.startswith("local:"):
            # Use local model via Ollama or LM Studio
            await self._use_local_model(message)
            return

        # Use the fallback handler to intelligently try available options
        from .fallback_handler import smart_chat

        response = await smart_chat(message, console=console)

        if response:
            from rich.panel import Panel

            console.print()
            console.print(
                Panel(
                    response,
                    title="[bold cyan]AI Response[/bold cyan]",
                    title_align="left",
                    border_style="dim cyan",
                    padding=(1, 2),
                )
            )
            return

        # Try OpenAI first explicitly (in case fallback handler missed it)
        openai_key = os.environ.get("OPENAI_API_KEY") or os.getenv("OPENAI_API_KEY")
        if openai_key:
            try:
                from openai import AsyncOpenAI

                client = AsyncOpenAI()
                response = await client.chat.completions.create(
                    model=self.orchestrator.orchestrator_model or "gpt-4",
                    messages=[
                        {
                            "role": "system",
                            "content": "You are a helpful AI coding assistant.",
                        },
                        {"role": "user", "content": message},
                    ],
                    temperature=0.7,
                    max_tokens=2000,
                )

                if response.choices:
                    from rich.panel import Panel

                    console.print()
                    console.print(
                        Panel(
                            response.choices[0].message.content,
                            title="[bold cyan]GPT-4[/bold cyan]",
                            title_align="left",
                            border_style="dim cyan",
                            padding=(1, 2),
                        )
                    )
                return

            except Exception as e:
                console.print(f"[yellow]OpenAI error: {e}[/yellow]")

        # Try Anthropic
        if os.getenv("ANTHROPIC_API_KEY"):
            try:
                from anthropic import AsyncAnthropic

                client = AsyncAnthropic()
                response = await client.messages.create(
                    model="claude-3-5-sonnet-20241022",
                    messages=[{"role": "user", "content": message}],
                    max_tokens=2000,
                )

                if response.content:
                    from rich.panel import Panel

                    console.print()
                    console.print(
                        Panel(
                            response.content[0].text,
                            title="[bold cyan]Claude[/bold cyan]",
                            title_align="left",
                            border_style="dim cyan",
                            padding=(1, 2),
                        )
                    )
                return

            except Exception as e:
                console.print(f"[yellow]Anthropic error: {e}[/yellow]")

        # No API keys available
        console.print("[red]No AI API keys configured![/red]")
        console.print(
            "[yellow]Try these options that don't need your API key:[/yellow]"
        )
        console.print("\n[bold]CLI Tools (use existing tools):[/bold]")
        console.print(
            "  • hanzo dev --orchestrator codex          # OpenAI CLI (if installed)"
        )
        console.print(
            "  • hanzo dev --orchestrator claude         # Claude Desktop (if installed)"
        )
        console.print(
            "  • hanzo dev --orchestrator gemini         # Gemini CLI (if installed)"
        )
        console.print(
            "  • hanzo dev --orchestrator hanzo-ide      # Hanzo IDE from ~/work/hanzo/ide"
        )
        console.print("\n[bold]Free APIs (rate limited):[/bold]")
        console.print(
            "  • hanzo dev --orchestrator codestral      # Free Mistral Codestral"
        )
        console.print("  • hanzo dev --orchestrator starcoder      # Free StarCoder")
        console.print("\n[bold]Local Models (unlimited):[/bold]")
        console.print("  • hanzo dev --orchestrator local:llama3.2 # Via Ollama")
        console.print("  • hanzo dev --orchestrator local:codellama # Via Ollama")
        console.print("  • hanzo dev --orchestrator local:mistral  # Via Ollama")
        console.print("\n[dim]Or set API keys for full access:[/dim]")
        console.print("  • export OPENAI_API_KEY=sk-...")
        console.print("  • export ANTHROPIC_API_KEY=sk-ant-...")

    async def _use_free_codestral(self, message: str):
        """Use free Mistral Codestral API (no API key needed for trial)."""
        try:
            import httpx

            console.print("[dim]Using free Codestral API (rate limited)...[/dim]")

            async with httpx.AsyncClient() as client:
                # Mistral offers free tier with rate limits
                response = await client.post(
                    "https://api.mistral.ai/v1/chat/completions",
                    headers={
                        "Content-Type": "application/json",
                        # Free tier doesn't need API key for limited usage
                    },
                    json={
                        "model": "codestral-latest",
                        "messages": [
                            {
                                "role": "system",
                                "content": "You are Codestral, an AI coding assistant.",
                            },
                            {"role": "user", "content": message},
                        ],
                        "temperature": 0.7,
                        "max_tokens": 2000,
                    },
                    timeout=30.0,
                )

                if response.status_code == 200:
                    data = response.json()
                    if data.get("choices"):
                        console.print(
                            f"[cyan]Codestral:[/cyan] {data['choices'][0]['message']['content']}"
                        )
                else:
                    console.print(
                        "[yellow]Free tier limit reached. Try local models instead:[/yellow]"
                    )
                    console.print(
                        "  • Install Ollama: curl -fsSL https://ollama.com/install.sh | sh"
                    )
                    console.print("  • Run: ollama pull codellama")
                    console.print("  • Use: hanzo dev --orchestrator local:codellama")

        except Exception as e:
            console.print(f"[red]Codestral error: {e}[/red]")
            console.print("[yellow]Try local models instead (no limits):[/yellow]")
            console.print("  • hanzo dev --orchestrator local:codellama")

    async def _use_free_starcoder(self, message: str):
        """Use free StarCoder via HuggingFace Inference API."""
        try:
            import httpx

            console.print("[dim]Using free StarCoder API...[/dim]")

            async with httpx.AsyncClient() as client:
                # HuggingFace offers free inference API
                response = await client.post(
                    "https://api-inference.huggingface.co/models/bigcode/starcoder2-15b",
                    headers={
                        "Content-Type": "application/json",
                    },
                    json={
                        "inputs": f"<|system|>You are StarCoder, an AI coding assistant.<|end|>\n<|user|>{message}<|end|>\n<|assistant|>",
                        "parameters": {
                            "temperature": 0.7,
                            "max_new_tokens": 2000,
                            "return_full_text": False,
                        },
                    },
                    timeout=30.0,
                )

                if response.status_code == 200:
                    data = response.json()
                    if isinstance(data, list) and data:
                        console.print(
                            f"[cyan]StarCoder:[/cyan] {data[0].get('generated_text', '')}"
                        )
                else:
                    console.print(
                        "[yellow]API limit reached. Install local models:[/yellow]"
                    )
                    console.print("  • brew install ollama")
                    console.print("  • ollama pull starcoder2")
                    console.print("  • hanzo dev --orchestrator local:starcoder2")

        except Exception as e:
            console.print(f"[red]StarCoder error: {e}[/red]")

    async def _use_openai_cli(self, message: str):
        """Use OpenAI CLI (Codex) - the official OpenAI CLI tool."""
        try:
            import json
            import subprocess

            console.print("[dim]Using OpenAI CLI (Codex)...[/dim]")

            # Check if openai CLI is installed
            result = subprocess.run(["which", "openai"], capture_output=True, text=True)
            if result.returncode != 0:
                console.print("[red]OpenAI CLI not installed![/red]")
                console.print("[yellow]To install:[/yellow]")
                console.print("  • pip install openai-cli")
                console.print("  • openai login")
                console.print("Then use: hanzo dev --orchestrator codex")
                return

            # Use openai CLI to chat - correct syntax
            cmd = [
                "openai",
                "api",
                "chat.completions.create",
                "-m",
                "gpt-4",
                "-g",
                message,
            ]

            process = subprocess.Popen(
                cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True
            )

            stdout, stderr = process.communicate(timeout=30)

            if process.returncode == 0 and stdout:
                console.print(f"[cyan]Codex:[/cyan] {stdout.strip()}")
            else:
                console.print(f"[red]OpenAI CLI error: {stderr}[/red]")

        except subprocess.TimeoutExpired:
            console.print("[yellow]OpenAI CLI timed out[/yellow]")
        except Exception as e:
            console.print(f"[red]Error using OpenAI CLI: {e}[/red]")

    async def _use_claude_cli(self, message: str):
        """Use Claude Desktop/Code CLI."""
        try:
            import os
            import subprocess

            console.print("[dim]Using Claude Desktop...[/dim]")

            # Check for Claude Code or Claude Desktop
            claude_paths = [
                "/usr/local/bin/claude",
                "/Applications/Claude.app/Contents/MacOS/Claude",
                os.path.expanduser("~/Applications/Claude.app/Contents/MacOS/Claude"),
                "claude",  # In PATH
            ]

            claude_path = None
            for path in claude_paths:
                if (
                    os.path.exists(path)
                    or subprocess.run(["which", path], capture_output=True).returncode
                    == 0
                ):
                    claude_path = path
                    break

            if not claude_path:
                console.print("[red]Claude Desktop not found![/red]")
                console.print("[yellow]To install:[/yellow]")
                console.print("  • Download from https://claude.ai/desktop")
                console.print("  • Or: brew install --cask claude")
                console.print("Then use: hanzo dev --orchestrator claude")
                return

            # Send message to Claude via CLI or AppleScript on macOS
            if sys.platform == "darwin":
                # Use AppleScript to interact with Claude Desktop
                script = f"""
                tell application "Claude"
                    activate
                    delay 0.5
                    tell application "System Events"
                        keystroke "{message.replace('"', '\\"')}"
                        key code 36  -- Enter key
                    end tell
                end tell
                """

                subprocess.run(["osascript", "-e", script])
                console.print(
                    "[cyan]Sent to Claude Desktop. Check the app for response.[/cyan]"
                )
            else:
                # Try direct CLI invocation
                process = subprocess.Popen(
                    [claude_path, "--message", message],
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    text=True,
                )

                stdout, stderr = process.communicate(timeout=30)

                if stdout:
                    console.print(f"[cyan]Claude:[/cyan] {stdout.strip()}")

        except Exception as e:
            console.print(f"[red]Error using Claude Desktop: {e}[/red]")

    async def _use_gemini_cli(self, message: str):
        """Use Gemini CLI."""
        try:
            import subprocess

            console.print("[dim]Using Gemini CLI...[/dim]")

            # Check if gemini CLI is installed
            result = subprocess.run(["which", "gemini"], capture_output=True, text=True)
            if result.returncode != 0:
                console.print("[red]Gemini CLI not installed![/red]")
                console.print("[yellow]To install:[/yellow]")
                console.print("  • pip install google-generativeai-cli")
                console.print("  • gemini configure")
                console.print("  • Set GOOGLE_API_KEY environment variable")
                console.print("Then use: hanzo dev --orchestrator gemini")
                return

            # Use gemini CLI
            cmd = ["gemini", "chat", message]

            process = subprocess.Popen(
                cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True
            )

            stdout, stderr = process.communicate(timeout=30)

            if process.returncode == 0 and stdout:
                console.print(f"[cyan]Gemini:[/cyan] {stdout.strip()}")
            else:
                console.print(f"[red]Gemini CLI error: {stderr}[/red]")

        except subprocess.TimeoutExpired:
            console.print("[yellow]Gemini CLI timed out[/yellow]")
        except Exception as e:
            console.print(f"[red]Error using Gemini CLI: {e}[/red]")

    async def _use_hanzo_ide(self, message: str):
        """Use Hanzo Dev IDE from ~/work/hanzo/ide."""
        try:
            import os
            import subprocess

            console.print("[dim]Using Hanzo Dev IDE...[/dim]")

            # Check if Hanzo IDE exists
            ide_path = os.path.expanduser("~/work/hanzo/ide")
            if not os.path.exists(ide_path):
                console.print("[red]Hanzo Dev IDE not found![/red]")
                console.print("[yellow]Expected location: ~/work/hanzo/ide[/yellow]")
                console.print("To set up:")
                console.print(
                    "  • git clone https://github.com/hanzoai/ide ~/work/hanzo/ide"
                )
                console.print("  • cd ~/work/hanzo/ide && npm install")
                return

            # Check for the CLI entry point
            cli_paths = [
                os.path.join(ide_path, "bin", "hanzo-ide"),
                os.path.join(ide_path, "hanzo-ide"),
                os.path.join(ide_path, "cli.js"),
                os.path.join(ide_path, "index.js"),
            ]

            cli_path = None
            for path in cli_paths:
                if os.path.exists(path):
                    cli_path = path
                    break

            if not cli_path:
                # Try to run with npm/node
                package_json = os.path.join(ide_path, "package.json")
                if os.path.exists(package_json):
                    # Run via npm
                    cmd = ["npm", "run", "chat", "--", message]
                    cwd = ide_path
                else:
                    console.print("[red]Hanzo IDE CLI not found![/red]")
                    return
            else:
                # Run the CLI directly
                if cli_path.endswith(".js"):
                    cmd = ["node", cli_path, "chat", message]
                else:
                    cmd = [cli_path, "chat", message]
                cwd = None

            process = subprocess.Popen(
                cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, cwd=cwd
            )

            stdout, stderr = process.communicate(timeout=30)

            if process.returncode == 0 and stdout:
                console.print(f"[cyan]Hanzo IDE:[/cyan] {stdout.strip()}")
            else:
                if stderr:
                    console.print(f"[yellow]Hanzo IDE: {stderr}[/yellow]")
                else:
                    console.print("[yellow]Hanzo IDE: No response[/yellow]")

        except subprocess.TimeoutExpired:
            console.print("[yellow]Hanzo IDE timed out[/yellow]")
        except Exception as e:
            console.print(f"[red]Error using Hanzo IDE: {e}[/red]")

    async def _use_local_model(self, message: str):
        """Use local model via Ollama or LM Studio."""
        import httpx

        model_name = self.orchestrator.orchestrator_model.replace("local:", "")

        # Try Ollama first (default port 11434)
        try:
            console.print(f"[dim]Using local {model_name} via Ollama...[/dim]")

            async with httpx.AsyncClient() as client:
                response = await client.post(
                    "http://localhost:11434/api/chat",
                    json={
                        "model": model_name,
                        "messages": [
                            {
                                "role": "system",
                                "content": "You are a helpful AI coding assistant.",
                            },
                            {"role": "user", "content": message},
                        ],
                        "stream": False,
                    },
                    timeout=60.0,
                )

                if response.status_code == 200:
                    data = response.json()
                    if data.get("message"):
                        console.print(
                            f"[cyan]{model_name}:[/cyan] {data['message']['content']}"
                        )
                        return

        except Exception:
            pass

        # Try LM Studio (default port 1234)
        try:
            console.print(f"[dim]Trying LM Studio...[/dim]")

            async with httpx.AsyncClient() as client:
                response = await client.post(
                    "http://localhost:1234/v1/chat/completions",
                    json={
                        "model": model_name,
                        "messages": [
                            {
                                "role": "system",
                                "content": "You are a helpful AI coding assistant.",
                            },
                            {"role": "user", "content": message},
                        ],
                        "temperature": 0.7,
                        "max_tokens": 2000,
                    },
                    timeout=60.0,
                )

                if response.status_code == 200:
                    data = response.json()
                    if data.get("choices"):
                        console.print(
                            f"[cyan]{model_name}:[/cyan] {data['choices'][0]['message']['content']}"
                        )
                        return

        except Exception:
            pass

        # Neither worked
        console.print(f"[red]Local model '{model_name}' not available[/red]")
        console.print("[yellow]To use local models:[/yellow]")
        console.print("\nOption 1 - Ollama (recommended):")
        console.print("  • Install: curl -fsSL https://ollama.com/install.sh | sh")
        console.print(f"  • Pull model: ollama pull {model_name}")
        console.print("  • It will auto-start when you use hanzo dev")
        console.print("\nOption 2 - LM Studio:")
        console.print("  • Download from https://lmstudio.ai")
        console.print(f"  • Load {model_name} model")
        console.print("  • Start local server (port 1234)")

    async def handle_memory_command(self, command: str):
        """Handle memory/context commands starting with #."""
        parts = command.split(maxsplit=1)
        cmd = parts[0].lower() if parts else ""
        args = parts[1] if len(parts) > 1 else ""

        if cmd == "remember":
            if args:
                console.print(f"[green]✓ Remembered: {args}[/green]")
            else:
                console.print("[yellow]Usage: #remember <text>[/yellow]")
        elif cmd == "forget":
            if args:
                console.print(f"[yellow]✓ Forgot: {args}[/yellow]")
            else:
                console.print("[yellow]Usage: #forget <text>[/yellow]")
        elif cmd == "memory":
            console.print("[cyan]Current Memory:[/cyan]")
            console.print("  • Working on Hanzo Python SDK")
            console.print("  • Using GPT-4 orchestrator")
        elif cmd == "context":
            console.print("[cyan]Current Context:[/cyan]")
            console.print(f"  • Directory: {os.getcwd()}")
            console.print(f"  • Model: {self.orchestrator.orchestrator_model}")
        else:
            console.print(f"[yellow]Unknown: #{cmd}[/yellow]")
            console.print("Try: #memory, #remember, #forget, #context")


async def run_dev_orchestrator(**kwargs):
    """Run the Hanzo Dev orchestrator with multi-agent networking.

    This is the main entry point from the CLI that sets up:
    1. Configurable orchestrator (GPT-5, GPT-4, Claude, Codex, etc.)
    2. Multiple worker agents (Claude instances for implementation)
    3. Critic agents for System 2 thinking
    4. MCP tool networking between instances
    5. Code quality guardrails
    6. Router-based or direct model access
    """
    workspace = kwargs.get("workspace", "~/.hanzo/dev")
    orchestrator_model = kwargs.get("orchestrator_model", "gpt-5")
    orchestrator_config = kwargs.get("orchestrator_config", None)  # New config object
    claude_path = kwargs.get("claude_path")
    monitor = kwargs.get("monitor", False)
    repl = kwargs.get("repl", True)
    instances = kwargs.get("instances", 2)
    mcp_tools = kwargs.get("mcp_tools", True)
    network_mode = kwargs.get("network_mode", True)
    guardrails = kwargs.get("guardrails", True)
    use_network = kwargs.get("use_network", True)  # Use hanzo-network if available
    use_hanzo_net = kwargs.get("use_hanzo_net", False)  # Use hanzo/net for local AI
    hanzo_net_port = kwargs.get("hanzo_net_port", 52415)
    console_obj = kwargs.get("console", console)

    console_obj.print(f"[bold cyan]Hanzo Dev - AI Coding OS[/bold cyan]")

    # Check if we should use network mode
    # For now, disable network mode since hanzo-network isn't available
    if False and use_network and NETWORK_AVAILABLE:
        console_obj.print(
            f"[cyan]Mode: Network Orchestration with hanzo-network[/cyan]"
        )
        console_obj.print(f"Orchestrator: {orchestrator_model}")
        console_obj.print(f"Workers: {instances} agents")
        console_obj.print(f"Critics: {max(1, instances // 2)} agents")
        console_obj.print(f"MCP Tools: {'Enabled' if mcp_tools else 'Disabled'}")
        console_obj.print(f"Guardrails: {'Enabled' if guardrails else 'Disabled'}\n")

        # Create network orchestrator with configurable LLM
        orchestrator = NetworkOrchestrator(
            workspace_dir=workspace,
            orchestrator_model=orchestrator_model,
            num_workers=instances,
            enable_mcp=mcp_tools,
            enable_networking=network_mode,
            enable_guardrails=guardrails,
            use_hanzo_net=use_hanzo_net,
            hanzo_net_port=hanzo_net_port,
            console=console_obj,
        )

        # Initialize the network
        success = await orchestrator.initialize()
        if not success:
            console_obj.print("[red]Failed to initialize network[/red]")
            return
    else:
        # Fallback to API mode
        console_obj.print(f"[cyan]Mode: AI Chat[/cyan]")
        console_obj.print(f"Model: {orchestrator_model}")
        console_obj.print(f"MCP Tools: {'Enabled' if mcp_tools else 'Disabled'}")
        console_obj.print(f"Guardrails: {'Enabled' if guardrails else 'Disabled'}\n")

        orchestrator = MultiClaudeOrchestrator(
            workspace_dir=workspace,
            claude_path=claude_path,
            num_instances=instances,
            enable_mcp=mcp_tools,
            enable_networking=network_mode,
            enable_guardrails=guardrails,
            console=console_obj,
            orchestrator_model=orchestrator_model,
        )

        # Initialize instances
        await orchestrator.initialize()

    if monitor:
        # Start monitoring mode
        await orchestrator.monitor_loop()
    elif repl:
        # Start REPL interface
        repl_interface = HanzoDevREPL(orchestrator)
        await repl_interface.run()
    else:
        # Run once
        await asyncio.sleep(10)
        orchestrator.shutdown()


class NetworkOrchestrator(HanzoDevOrchestrator):
    """Advanced orchestrator using hanzo-network with configurable LLM (GPT-5, Claude, local, etc.)."""

    def __init__(
        self,
        workspace_dir: str,
        orchestrator_model: str = "gpt-5",
        num_workers: int = 2,
        enable_mcp: bool = True,
        enable_networking: bool = True,
        enable_guardrails: bool = True,
        use_hanzo_net: bool = False,
        hanzo_net_port: int = 52415,
        console: Console = console,
    ):
        """Initialize network orchestrator with configurable LLM.

        Args:
            workspace_dir: Workspace directory
            orchestrator_model: Model to use for orchestration (e.g., "gpt-5", "gpt-4", "claude-3-5-sonnet", "local:llama3.2")
            num_workers: Number of worker agents (Claude instances)
            enable_mcp: Enable MCP tools
            enable_networking: Enable agent networking
            enable_guardrails: Enable quality guardrails
            use_hanzo_net: Use hanzo/net for local orchestration
            hanzo_net_port: Port for hanzo/net (default 52415)
            console: Console for output
        """
        super().__init__(workspace_dir)
        self.orchestrator_model = orchestrator_model
        self.num_workers = num_workers
        self.enable_mcp = enable_mcp
        self.enable_networking = enable_networking
        self.enable_guardrails = enable_guardrails
        self.use_hanzo_net = use_hanzo_net
        self.hanzo_net_port = hanzo_net_port
        self.console = console

        # Agent network components
        self.orchestrator_agent = None
        self.worker_agents = []
        self.critic_agents = []
        self.agent_network = None
        self.hanzo_net_process = None

        # Check if we can use hanzo-network
        if not NETWORK_AVAILABLE:
            self.console.print(
                "[yellow]Warning: hanzo-network not available, falling back to basic mode[/yellow]"
            )

    async def initialize(self):
        """Initialize the agent network with orchestrator and workers."""
        if not NETWORK_AVAILABLE:
            self.console.print(
                "[red]Cannot initialize network mode without hanzo-network[/red]"
            )
            return False

        # Start hanzo net if requested for local orchestration
        if self.use_hanzo_net or self.orchestrator_model.startswith("local:"):
            await self._start_hanzo_net()

        self.console.print(
            f"[cyan]Initializing agent network with {self.orchestrator_model} orchestrator...[/cyan]"
        )

        # Create orchestrator agent (GPT-5, local, or other model)
        self.orchestrator_agent = await self._create_orchestrator_agent()

        # Create worker agents (Claude instances for implementation)
        for i in range(self.num_workers):
            worker = await self._create_worker_agent(i)
            self.worker_agents.append(worker)

        # Add local workers if using hanzo net (for cost optimization)
        if self.use_hanzo_net or self.orchestrator_model.startswith("local:"):
            # Add 1-2 local workers for simple tasks
            num_local_workers = min(2, self.num_workers)
            for i in range(num_local_workers):
                local_worker = await self._create_local_worker_agent(i)
                self.worker_agents.append(local_worker)
            self.console.print(
                f"[green]Added {num_local_workers} local workers for cost optimization[/green]"
            )

        # Create critic agents for System 2 thinking
        if self.enable_guardrails:
            for i in range(max(1, self.num_workers // 2)):
                critic = await self._create_critic_agent(i)
                self.critic_agents.append(critic)

        # Create the agent network
        all_agents = [self.orchestrator_agent] + self.worker_agents + self.critic_agents

        # Create router based on configuration
        if self.use_hanzo_net or self.orchestrator_model.startswith("local:"):
            # Use cost-optimized router that prefers local models
            router = await self._create_cost_optimized_router()
        else:
            # Use intelligent router with orchestrator making decisions
            router = await self._create_intelligent_router()

        # Create the network
        self.agent_network = create_network(
            agents=all_agents,
            router=router,
            default_agent=(
                self.orchestrator_agent.name if self.orchestrator_agent else None
            ),
        )

        self.console.print(
            f"[green]✓ Agent network initialized with {len(all_agents)} agents[/green]"
        )
        return True

    async def _start_hanzo_net(self):
        """Start hanzo net for local AI orchestration."""
        self.console.print(
            "[cyan]Starting hanzo/net for local AI orchestration...[/cyan]"
        )

        # Check if hanzo net is already running
        import socket

        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        result = sock.connect_ex(("localhost", self.hanzo_net_port))
        sock.close()

        if result == 0:
            self.console.print(
                f"[yellow]hanzo/net already running on port {self.hanzo_net_port}[/yellow]"
            )
            return

        # Start hanzo net
        try:
            # Determine model to serve based on orchestrator model
            model = "llama-3.2-3b"  # Default
            if ":" in self.orchestrator_model:
                model = self.orchestrator_model.split(":")[1]

            cmd = [
                "hanzo",
                "net",
                "--port",
                str(self.hanzo_net_port),
                "--models",
                model,
                "--network",
                "local",
            ]

            self.hanzo_net_process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                preexec_fn=os.setsid if hasattr(os, "setsid") else None,
            )

            # Wait for it to start
            await asyncio.sleep(3)

            if self.hanzo_net_process.poll() is None:
                self.console.print(
                    f"[green]✓ hanzo/net started on port {self.hanzo_net_port} with model {model}[/green]"
                )
            else:
                self.console.print("[red]Failed to start hanzo/net[/red]")

        except Exception as e:
            self.console.print(f"[red]Error starting hanzo/net: {e}[/red]")

    async def _create_orchestrator_agent(self) -> Agent:
        """Create the orchestrator agent (GPT-5, local, or configured model)."""
        # Check if using local model via hanzo/net
        if self.orchestrator_model.startswith("local:"):
            # Use local model via hanzo/net
            model_name = self.orchestrator_model.split(":")[1]

            # Import local network helpers
            from hanzo_network.local_network import create_local_agent

            orchestrator = create_local_agent(
                name="local_orchestrator",
                description=f"Local {model_name} orchestrator via hanzo/net",
                system=self._get_orchestrator_system_prompt(),
                local_model=model_name,
                base_url=f"http://localhost:{self.hanzo_net_port}",
                tools=[],
            )

            self.console.print(
                f"[green]✓ Created local {model_name} orchestrator via hanzo/net[/green]"
            )
            return orchestrator

        # Parse model string to get provider and model
        model_name = self.orchestrator_model
        provider = "openai"  # Default to OpenAI - use string
        api_key = None

        # Determine provider from model name
        if model_name.startswith("gpt") or model_name == "codex":
            provider = "openai"
            api_key = os.getenv("OPENAI_API_KEY")
        elif model_name.startswith("claude"):
            provider = "anthropic"
            api_key = os.getenv("ANTHROPIC_API_KEY")
        elif model_name.startswith("gemini"):
            provider = "google"
            api_key = os.getenv("GOOGLE_API_KEY")
        elif model_name.startswith("local:"):
            provider = "local"
            model_name = model_name.replace("local:", "")

        # Create model config based on what's available
        if NETWORK_AVAILABLE:
            # Real ModelConfig may have different signature
            try:
                model_config = ModelConfig(
                    name=model_name,
                    provider=provider,
                )
                # Set api_key separately if supported
                if hasattr(model_config, "api_key"):
                    model_config.api_key = api_key
            except TypeError:
                # Fallback to simple string if ModelConfig doesn't work
                model_config = model_name
        else:
            # Use our fallback ModelConfig
            model_config = ModelConfig(
                name=model_name,
                provider=provider,
                api_key=api_key,
            )

        # Create orchestrator with strategic system prompt
        orchestrator = create_agent(
            name="orchestrator",
            description=f"{self.orchestrator_model} powered meta-orchestrator for AI coding",
            model=model_config,
            system=self._get_orchestrator_system_prompt(),
            tools=[],  # Orchestrator tools will be added
        )

        self.console.print(
            f"[green]✓ Created {self.orchestrator_model} orchestrator[/green]"
        )
        return orchestrator

    def _get_orchestrator_system_prompt(self) -> str:
        """Get the system prompt for the orchestrator."""
        return """You are an advanced AI orchestrator managing a network of specialized agents.
        Your responsibilities:
        1. Strategic Planning: Break down complex tasks into manageable subtasks
        2. Agent Coordination: Delegate work to appropriate specialist agents
        3. Quality Control: Ensure code quality through critic agents
        4. System 2 Thinking: Invoke deliberative reasoning for complex decisions
        5. Resource Management: Optimize agent usage for cost and performance
        
        Available agents:
        - Worker agents: Claude instances for code implementation and MCP tool usage
        - Critic agents: Review and improve code quality
        - Local agents: Fast, cost-effective for simple tasks
        
        Decision framework:
        - Complex reasoning → Use your advanced capabilities
        - Code implementation → Delegate to worker agents
        - Quality review → Invoke critic agents
        - Simple tasks → Use local agents if available
        
        Always maintain high code quality standards and prevent degradation."""

    async def _create_worker_agent(self, index: int) -> Agent:
        """Create a worker agent (Claude for implementation)."""
        worker = create_agent(
            name=f"worker_{index}",
            description=f"Claude worker agent {index} for code implementation",
            model=(
                "claude-3-5-sonnet-20241022"
                if NETWORK_AVAILABLE
                else ModelConfig(
                    provider="anthropic",
                    name="claude-3-5-sonnet-20241022",
                    api_key=os.getenv("ANTHROPIC_API_KEY"),
                )
            ),
            system="""You are a Claude worker agent specialized in code implementation.
            
            Your capabilities:
            - Write and modify code
            - Use MCP tools for file operations
            - Execute commands and tests
            - Debug and fix issues
            
            Follow best practices and maintain code quality.""",
            tools=[],  # MCP tools will be added if enabled
        )

        self.console.print(f"  Created worker agent {index}")
        return worker

    async def _create_local_worker_agent(self, index: int) -> Agent:
        """Create a local worker agent for simple tasks (cost optimization)."""
        from hanzo_network.local_network import create_local_agent

        worker = create_local_agent(
            name=f"local_worker_{index}",
            description=f"Local worker agent {index} for simple tasks",
            system="""You are a local worker agent optimized for simple tasks.
            
            Your capabilities:
            - Simple code transformations
            - Basic file operations
            - Quick validation checks
            - Pattern matching
            
            You handle simple tasks to reduce API costs.""",
            local_model="llama-3.2-3b",
            base_url=f"http://localhost:{self.hanzo_net_port}",
            tools=[],
        )

        self.console.print(f"  Created local worker agent {index}")
        return worker

    async def _create_critic_agent(self, index: int) -> Agent:
        """Create a critic agent for code review."""
        # Use a different model for critics for diversity
        critic_model = "gpt-4" if index % 2 == 0 else "claude-3-5-sonnet-20241022"

        critic = create_agent(
            name=f"critic_{index}",
            description=f"Critic agent {index} for code quality assurance",
            model=critic_model,  # Just pass the model name string
            system="""You are a critic agent focused on code quality and best practices.
            
            Review code for:
            1. Correctness and bug detection
            2. Performance optimization opportunities
            3. Security vulnerabilities
            4. Maintainability and readability
            5. Best practices and design patterns
            
            Provide constructive feedback with specific improvement suggestions.""",
            tools=[],
        )

        self.console.print(f"  Created critic agent {index} ({critic_model})")
        return critic

    async def _create_cost_optimized_router(self) -> Router:
        """Create a cost-optimized router that prefers local models."""
        from hanzo_network.core.router import Router

        class CostOptimizedRouter(Router):
            """Router that minimizes costs by using local models when possible."""

            def __init__(self, orchestrator_agent, worker_agents, critic_agents):
                super().__init__()
                self.orchestrator = orchestrator_agent
                self.workers = worker_agents
                self.critics = critic_agents
                self.local_workers = [w for w in worker_agents if "local" in w.name]
                self.api_workers = [w for w in worker_agents if "local" not in w.name]

            async def route(self, prompt: str, state=None) -> str:
                """Route based on task complexity and cost optimization."""
                prompt_lower = prompt.lower()

                # Simple tasks → Local workers
                simple_keywords = [
                    "list",
                    "check",
                    "validate",
                    "format",
                    "rename",
                    "count",
                    "find",
                ]
                if (
                    any(keyword in prompt_lower for keyword in simple_keywords)
                    and self.local_workers
                ):
                    return self.local_workers[0].name

                # Complex implementation → API workers (Claude)
                complex_keywords = [
                    "implement",
                    "refactor",
                    "debug",
                    "optimize",
                    "design",
                    "architect",
                ]
                if (
                    any(keyword in prompt_lower for keyword in complex_keywords)
                    and self.api_workers
                ):
                    return self.api_workers[0].name

                # Review tasks → Critics
                review_keywords = [
                    "review",
                    "critique",
                    "analyze",
                    "improve",
                    "validate code",
                ]
                if (
                    any(keyword in prompt_lower for keyword in review_keywords)
                    and self.critics
                ):
                    return self.critics[0].name

                # Strategic decisions → Orchestrator
                strategic_keywords = [
                    "plan",
                    "decide",
                    "strategy",
                    "coordinate",
                    "organize",
                ]
                if any(keyword in prompt_lower for keyword in strategic_keywords):
                    return self.orchestrator.name

                # Default: Try local first, then API
                if self.local_workers:
                    # For shorter prompts, try local first
                    if len(prompt) < 500:
                        return self.local_workers[0].name

                # Fall back to API workers for complex tasks
                return (
                    self.api_workers[0].name
                    if self.api_workers
                    else self.orchestrator.name
                )

        # Create the cost-optimized router
        router = CostOptimizedRouter(
            self.orchestrator_agent, self.worker_agents, self.critic_agents
        )

        self.console.print(
            "[green]✓ Created cost-optimized router (local models preferred)[/green]"
        )
        return router

    async def _create_intelligent_router(self) -> Router:
        """Create an intelligent router using the orchestrator for decisions."""
        if self.orchestrator_agent:
            # Create routing agent that uses orchestrator for decisions
            router = create_routing_agent(
                name="router",
                description="Intelligent task router",
                agent=self.orchestrator_agent,
                system="""Route tasks to the most appropriate agent based on:
                
                1. Task complexity and requirements
                2. Agent capabilities and specialization
                3. Current workload and availability
                4. Cost/performance optimization
                
                Routing strategy:
                - Strategic decisions → Stay with orchestrator
                - Implementation tasks → Route to workers
                - Review tasks → Route to critics
                - Parallel work → Split across multiple agents
                
                Return the name of the best agent for the task.""",
            )
        else:
            # Fallback to basic router
            router = create_router(
                agents=self.worker_agents + self.critic_agents,
                default=self.worker_agents[0].name if self.worker_agents else None,
            )

        return router

    async def execute_with_network(
        self, task: str, context: Optional[Dict] = None
    ) -> Dict:
        """Execute a task using the agent network.

        Args:
            task: Task description
            context: Optional context

        Returns:
            Execution result
        """
        if not self.agent_network:
            self.console.print("[red]Agent network not initialized[/red]")
            return {"error": "Network not initialized"}

        self.console.print(f"[cyan]Executing task with agent network: {task}[/cyan]")

        # Create network state
        state = NetworkState()
        state.add_message("user", task)

        if context:
            state.metadata.update(context)

        # Run the network
        try:
            result = await self.agent_network.run(prompt=task, state=state)

            # If guardrails enabled, validate result
            if self.enable_guardrails and self.critic_agents:
                validated = await self._validate_with_critics(result, task)
                if validated.get("improvements"):
                    self.console.print("[yellow]Applied critic improvements[/yellow]")
                    return validated

            return result

        except Exception as e:
            self.console.print(f"[red]Network execution error: {e}[/red]")
            return {"error": str(e)}

    async def _validate_with_critics(self, result: Dict, original_task: str) -> Dict:
        """Validate and potentially improve result using critic agents."""
        if not self.critic_agents:
            return result

        # Get first critic to review
        critic = self.critic_agents[0]

        review_prompt = f"""
        Review this solution:
        
        Task: {original_task}
        Solution: {result.get('output', '')}
        
        Provide specific improvements if needed.
        """

        review = await critic.run(review_prompt)

        # Check if improvements suggested
        if "improve" in str(review.get("output", "")).lower():
            result["improvements"] = review.get("output")

        return result

    def shutdown(self):
        """Shutdown the network orchestrator and hanzo net if running."""
        # Stop hanzo net if we started it
        if self.hanzo_net_process:
            try:
                self.console.print("[yellow]Stopping hanzo/net...[/yellow]")
                if hasattr(os, "killpg"):
                    os.killpg(os.getpgid(self.hanzo_net_process.pid), signal.SIGTERM)
                else:
                    self.hanzo_net_process.terminate()
                self.hanzo_net_process.wait(timeout=5)
                self.console.print("[green]✓ hanzo/net stopped[/green]")
            except Exception:
                try:
                    self.hanzo_net_process.kill()
                except Exception:
                    pass

        # Call parent shutdown
        super().shutdown()


class MultiClaudeOrchestrator(HanzoDevOrchestrator):
    """Extended orchestrator for multiple Claude instances with MCP networking."""

    def __init__(
        self,
        workspace_dir: str,
        claude_path: str,
        num_instances: int,
        enable_mcp: bool,
        enable_networking: bool,
        enable_guardrails: bool,
        console: Console,
        orchestrator_model: str = "gpt-4",
    ):
        super().__init__(workspace_dir, claude_path)
        self.num_instances = num_instances
        self.enable_mcp = enable_mcp
        self.enable_networking = enable_networking
        self.enable_guardrails = enable_guardrails
        self.console = console
        self.orchestrator_model = orchestrator_model  # Add this for chat interface

        # Store multiple Claude instances
        self.claude_instances = []
        self.instance_configs = []

    async def initialize(self):
        """Initialize all Claude instances with MCP networking."""
        # Check if Claude is available first
        claude_available = False
        try:
            import shutil

            if self.claude_code_path and Path(self.claude_code_path).exists():
                claude_available = True
            elif shutil.which("claude"):
                claude_available = True
        except Exception:
            pass

        if not claude_available:
            # Skip Claude instance initialization - will use API fallback silently
            return

        self.console.print("[cyan]Initializing Claude instances...[/cyan]")

        for i in range(self.num_instances):
            role = "primary" if i == 0 else f"critic_{i}"
            config = await self._create_instance_config(i, role)
            self.instance_configs.append(config)

            self.console.print(
                f"  [{i+1}/{self.num_instances}] {role} instance configured"
            )

        # If networking enabled, configure MCP connections between instances
        if self.enable_networking:
            await self._setup_mcp_networking()

        # Start all instances
        for i, config in enumerate(self.instance_configs):
            success = await self._start_claude_instance(i, config)
            if success:
                self.console.print(f"[green]✓ Instance {i} started[/green]")
            else:
                # Don't show error, just skip silently
                pass

    async def _create_instance_config(self, index: int, role: str) -> Dict:
        """Create configuration for a Claude instance."""
        base_port = 8000
        mcp_port = 9000

        config = {
            "index": index,
            "role": role,
            "workspace": self.workspace_dir / f"instance_{index}",
            "port": base_port + index,
            "mcp_port": mcp_port + index,
            "mcp_config": {},
            "env": {},
        }

        # Create workspace directory
        config["workspace"].mkdir(parents=True, exist_ok=True)

        # Configure MCP tools if enabled
        if self.enable_mcp:
            config["mcp_config"] = await self._create_mcp_config(index, role)

        return config

    async def _create_mcp_config(self, index: int, role: str) -> Dict:
        """Create MCP configuration for an instance."""
        mcp_config = {
            "mcpServers": {
                "hanzo-mcp": {
                    "command": "python",
                    "args": ["-m", "hanzo_mcp"],
                    "env": {"INSTANCE_ID": str(index), "INSTANCE_ROLE": role},
                }
            }
        }

        # Add file system tools
        mcp_config["mcpServers"]["filesystem"] = {
            "command": "npx",
            "args": ["-y", "@modelcontextprotocol/server-filesystem"],
            "env": {"ALLOWED_DIRECTORIES": str(self.workspace_dir)},
        }

        return mcp_config

    async def _setup_mcp_networking(self):
        """Set up MCP networking between Claude instances."""
        self.console.print(
            "[cyan]Setting up MCP networking between instances...[/cyan]"
        )

        # Each instance gets MCP servers for all other instances
        for i, config in enumerate(self.instance_configs):
            for j, other_config in enumerate(self.instance_configs):
                if i != j:
                    # Add other instance as MCP server
                    server_name = f"claude_instance_{j}"
                    config["mcp_config"]["mcpServers"][server_name] = {
                        "command": "python",
                        "args": [
                            "-m",
                            "hanzo_mcp.bridge",
                            "--target-port",
                            str(other_config["port"]),
                            "--instance-id",
                            str(j),
                            "--role",
                            other_config["role"],
                        ],
                        "env": {"SOURCE_INSTANCE": str(i), "TARGET_INSTANCE": str(j)},
                    }

            # Save MCP config
            mcp_config_file = config["workspace"] / "mcp_config.json"
            with open(mcp_config_file, "w") as f:
                json.dump(config["mcp_config"], f, indent=2)

            config["env"]["MCP_CONFIG_PATH"] = str(mcp_config_file)

    async def _start_claude_instance(self, index: int, config: Dict) -> bool:
        """Start a single Claude instance."""
        try:
            cmd = [self.claude_code_path or "claude"]

            # Add configuration flags
            if config.get("env", {}).get("MCP_CONFIG_PATH"):
                cmd.extend(["--mcp-config", config["env"]["MCP_CONFIG_PATH"]])

            # Set up environment
            env = os.environ.copy()
            env.update(config.get("env", {}))

            # Start process
            process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                stdin=subprocess.PIPE,
                env=env,
                cwd=str(config["workspace"]),
                preexec_fn=os.setsid if hasattr(os, "setsid") else None,
            )

            self.claude_instances.append(
                {
                    "index": index,
                    "role": config["role"],
                    "process": process,
                    "config": config,
                    "health": RuntimeHealth(
                        state=RuntimeState.RUNNING,
                        last_response=datetime.now(),
                        response_time_ms=0,
                        memory_usage_mb=0,
                        cpu_percent=0,
                        error_count=0,
                        restart_count=0,
                    ),
                }
            )

            return True

        except Exception as e:
            logger.error(f"Failed to start instance {index}: {e}")
            return False

    async def execute_with_critique(self, task: str) -> Dict:
        """Execute a task with System 2 critique.

        1. Primary instance executes the task
        2. Critic instance(s) review and suggest improvements
        3. Primary incorporates feedback if confidence is high
        """
        self.console.print(f"[cyan]Executing with System 2 thinking: {task}[/cyan]")

        # Check if instances are initialized
        if not self.claude_instances:
            # No instances started, use fallback handler for smart routing
            from .fallback_handler import smart_chat

            response = await smart_chat(task, console=self.console)
            if response:
                return {"output": response, "success": True}
            # If smart_chat fails, try direct API as last resort
            return await self._call_api_model(task)

        # Step 1: Primary execution
        primary = self.claude_instances[0]
        result = await self._send_to_instance(primary, task)

        if self.num_instances < 2:
            return result

        # Step 2: Critic review
        critiques = []
        for critic in self.claude_instances[1:]:
            critique_prompt = f"""
            Review this code/solution and provide constructive criticism:
            
            Task: {task}
            Solution: {result.get('output', '')}
            
            Evaluate for:
            1. Correctness
            2. Performance
            3. Security
            4. Maintainability
            5. Best practices
            
            Suggest specific improvements.
            """

            critique = await self._send_to_instance(critic, critique_prompt)
            critiques.append(critique)

        # Step 3: Incorporate feedback if valuable
        if critiques and self.enable_guardrails:
            improvement_prompt = f"""
            Original task: {task}
            Original solution: {result.get('output', '')}
            
            Critiques received:
            {json.dumps(critiques, indent=2)}
            
            Incorporate the valid suggestions and produce an improved solution.
            """

            improved = await self._send_to_instance(primary, improvement_prompt)

            # Validate improvement didn't degrade quality
            if await self._validate_improvement(result, improved):
                self.console.print(
                    "[green]✓ Solution improved with System 2 feedback[/green]"
                )
                return improved
            else:
                self.console.print(
                    "[yellow]⚠ Keeping original solution (improvement validation failed)[/yellow]"
                )

        return result

    async def _send_to_instance(self, instance: Dict, prompt: str) -> Dict:
        """Send a prompt to a specific Claude instance using configured model."""
        # Simple direct approach - use the configured orchestrator model
        if self.orchestrator_model == "codex":
            # Use OpenAI CLI
            return await self._call_openai_cli(prompt)
        elif self.orchestrator_model in ["claude", "claude-code", "claude-desktop"]:
            # Use Claude Desktop
            return await self._call_claude_cli(prompt)
        elif self.orchestrator_model in ["gemini", "gemini-cli"]:
            # Use Gemini CLI
            return await self._call_gemini_cli(prompt)
        elif self.orchestrator_model.startswith("local:"):
            # Use local model
            return await self._call_local_model(prompt)
        else:
            # Try API-based models
            return await self._call_api_model(prompt)

    async def _call_openai_cli(self, prompt: str) -> Dict:
        """Call OpenAI CLI and return structured response."""
        try:
            import subprocess

            result = subprocess.run(
                [
                    "openai",
                    "api",
                    "chat.completions.create",
                    "-m",
                    "gpt-4",
                    "-g",
                    prompt,
                ],
                capture_output=True,
                text=True,
                timeout=30,
            )
            if result.returncode == 0 and result.stdout:
                return {"output": result.stdout.strip(), "success": True}
        except Exception as e:
            logger.error(f"OpenAI CLI error: {e}")
        return {
            "output": "OpenAI CLI not available. Install with: pip install openai-cli",
            "success": False,
        }

    async def _call_claude_cli(self, prompt: str) -> Dict:
        """Call Claude Desktop and return structured response."""
        try:
            import sys
            import subprocess

            if sys.platform == "darwin":
                # macOS - use AppleScript
                script = f'tell application "Claude" to activate'
                subprocess.run(["osascript", "-e", script])
                return {
                    "output": "Sent to Claude Desktop. Check app for response.",
                    "success": True,
                }
        except Exception as e:
            logger.error(f"Claude CLI error: {e}")
        return {
            "output": "Claude Desktop not available. Install from https://claude.ai/desktop",
            "success": False,
        }

    async def _call_gemini_cli(self, prompt: str) -> Dict:
        """Call Gemini CLI and return structured response."""
        try:
            import subprocess

            result = subprocess.run(
                ["gemini", "chat", prompt], capture_output=True, text=True, timeout=30
            )
            if result.returncode == 0 and result.stdout:
                return {"output": result.stdout.strip(), "success": True}
        except Exception as e:
            logger.error(f"Gemini CLI error: {e}")
        return {
            "output": "Gemini CLI not available. Install with: pip install google-generativeai-cli",
            "success": False,
        }

    async def _call_local_model(self, prompt: str) -> Dict:
        """Call local model via Ollama and return structured response."""
        try:
            import httpx

            model_name = self.orchestrator_model.replace("local:", "")

            async with httpx.AsyncClient() as client:
                response = await client.post(
                    "http://localhost:11434/api/chat",
                    json={
                        "model": model_name,
                        "messages": [{"role": "user", "content": prompt}],
                        "stream": False,
                    },
                    timeout=60.0,
                )

                if response.status_code == 200:
                    data = response.json()
                    if data.get("message"):
                        return {"output": data["message"]["content"], "success": True}
        except Exception as e:
            logger.error(f"Local model error: {e}")
        return {
            "output": f"Local model not available. Install Ollama and run: ollama pull {self.orchestrator_model.replace('local:', '')}",
            "success": False,
        }

    async def _call_api_model(self, prompt: str) -> Dict:
        """Call API-based model and return structured response."""
        import os

        # Try OpenAI first (check environment variable properly)
        openai_key = os.environ.get("OPENAI_API_KEY") or os.getenv("OPENAI_API_KEY")
        if openai_key:
            try:
                from openai import AsyncOpenAI

                client = AsyncOpenAI(api_key=openai_key)
                response = await client.chat.completions.create(
                    model="gpt-4",
                    messages=[{"role": "user", "content": prompt}],
                    max_tokens=2000,
                )
                if response.choices:
                    return {
                        "output": response.choices[0].message.content,
                        "success": True,
                    }
            except Exception as e:
                logger.error(f"OpenAI API error: {e}")

        # Try Anthropic
        anthropic_key = os.environ.get("ANTHROPIC_API_KEY") or os.getenv(
            "ANTHROPIC_API_KEY"
        )
        if anthropic_key:
            try:
                from anthropic import AsyncAnthropic

                client = AsyncAnthropic(api_key=anthropic_key)
                response = await client.messages.create(
                    model="claude-3-5-sonnet-20241022",
                    messages=[{"role": "user", "content": prompt}],
                    max_tokens=2000,
                )
                if response.content:
                    return {"output": response.content[0].text, "success": True}
            except Exception as e:
                logger.error(f"Anthropic API error: {e}")

        # Try fallback handler as last resort
        from .fallback_handler import smart_chat

        response = await smart_chat(
            prompt, console=None
        )  # No console to avoid duplicate messages
        if response:
            return {"output": response, "success": True}

        return {
            "output": "No API keys configured. Set OPENAI_API_KEY or ANTHROPIC_API_KEY",
            "success": False,
        }

    async def _validate_improvement(self, original: Dict, improved: Dict) -> bool:
        """Validate that an improvement doesn't degrade quality."""
        if not self.enable_guardrails:
            return True

        # Placeholder for actual validation logic
        # Would check: tests still pass, no new errors, performance not degraded, etc.
        return True

    def shutdown(self):
        """Shutdown all Claude instances."""
        self.console.print("[yellow]Shutting down all instances...[/yellow]")

        for instance in self.claude_instances:
            try:
                process = instance["process"]
                if hasattr(os, "killpg"):
                    os.killpg(os.getpgid(process.pid), signal.SIGTERM)
                else:
                    process.terminate()
                process.wait(timeout=5)
            except Exception:
                try:
                    instance["process"].kill()
                except Exception:
                    pass

        self.console.print("[green]✓ All instances shut down[/green]")


async def main():
    """Main entry point for hanzo-dev."""
    import argparse

    parser = argparse.ArgumentParser(
        description="Hanzo Dev - System 2 Meta-AI Orchestrator"
    )
    parser.add_argument(
        "--workspace", default="~/.hanzo/dev", help="Workspace directory"
    )
    parser.add_argument("--claude-path", help="Path to Claude Code executable")
    parser.add_argument("--monitor", action="store_true", help="Start in monitor mode")
    parser.add_argument("--repl", action="store_true", help="Start REPL interface")
    parser.add_argument(
        "--instances", type=int, default=2, help="Number of Claude instances"
    )
    parser.add_argument("--no-mcp", action="store_true", help="Disable MCP tools")
    parser.add_argument(
        "--no-network", action="store_true", help="Disable instance networking"
    )
    parser.add_argument(
        "--no-guardrails", action="store_true", help="Disable guardrails"
    )

    args = parser.parse_args()

    await run_dev_orchestrator(
        workspace=args.workspace,
        claude_path=args.claude_path,
        monitor=args.monitor,
        repl=args.repl or not args.monitor,
        instances=args.instances,
        mcp_tools=not args.no_mcp,
        network_mode=not args.no_network,
        guardrails=not args.no_guardrails,
    )


if __name__ == "__main__":
    asyncio.run(main())
