#!/usr/bin/env python3
"""
Comprehensive demo script for Hanzo Dev - AI Coding OS.
This demonstrates all features and orchestrator modes.
"""

import asyncio
import os
import sys
from pathlib import Path
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.prompt import Prompt
from rich import print as rprint

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "pkg" / "hanzo" / "src"))

from hanzo.dev import HanzoDevREPL, MultiClaudeOrchestrator
from hanzo.orchestrator_config import get_orchestrator_config

console = Console()

async def demo_chat_interface():
    """Demo the chat-first interface."""
    console.print("\n[bold cyan]═══ DEMO: Chat-First Interface ═══[/bold cyan]\n")
    
    console.print("The REPL is [bold]chat-first by default[/bold]:")
    console.print("• Type naturally to chat with AI")
    console.print("• Use [cyan]/commands[/cyan] for special actions")
    console.print("• Use [cyan]#memory[/cyan] to manage context")
    
    # Simulate chat interaction
    console.print("\n[dim]Example interaction:[/dim]")
    console.print("[dim white]╭" + "─" * 60 + "╮[/dim white]")
    console.print("[dim white]│[/dim white] › Write a Python function to calculate fibonacci")
    console.print("[dim white]╰" + "─" * 60 + "╯[/dim white]")
    
    await asyncio.sleep(1)
    
    console.print("\n[dim]AI Response:[/dim]")
    response = """def fibonacci(n):
    \"\"\"Calculate the nth Fibonacci number.\"\"\"
    if n <= 0:
        return 0
    elif n == 1:
        return 1
    else:
        return fibonacci(n-1) + fibonacci(n-2)"""
    
    console.print(Panel(response, title="[bold cyan]AI Response[/bold cyan]", 
                       title_align="left", border_style="dim cyan"))

async def demo_orchestrator_modes():
    """Demo different orchestrator modes."""
    console.print("\n[bold cyan]═══ DEMO: Orchestrator Modes ═══[/bold cyan]\n")
    
    # Create a table of orchestrator modes
    table = Table(title="Available Orchestrators", show_header=True, 
                  header_style="bold magenta")
    table.add_column("Mode", style="cyan", width=20)
    table.add_column("Description", width=50)
    table.add_column("Requirements", style="yellow")
    
    modes = [
        ("gpt-5", "Ultimate code development AI", "OPENAI_API_KEY"),
        ("gpt-4", "Production-ready OpenAI model", "OPENAI_API_KEY"),
        ("claude", "Anthropic's Claude 3.5 Sonnet", "ANTHROPIC_API_KEY"),
        ("codex", "OpenAI CLI (no API key needed)", "OpenAI CLI installed"),
        ("local:llama3.2", "Local Llama model", "Ollama installed"),
        ("gpt-5-pro-codex", "Hybrid mode with Codex", "Multiple tools"),
        ("router:gpt-4", "Via Hanzo router", "Router configured"),
        ("direct:claude", "Direct API access", "API key required"),
    ]
    
    for mode, desc, req in modes:
        table.add_row(mode, desc, req)
    
    console.print(table)
    
    # Test each mode
    console.print("\n[bold]Testing orchestrator configurations:[/bold]")
    
    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console,
    ) as progress:
        for mode, _, _ in modes:
            task = progress.add_task(f"Testing {mode}...", total=None)
            try:
                config = get_orchestrator_config(mode)
                await asyncio.sleep(0.5)  # Simulate test
                progress.update(task, description=f"✓ {mode} configured")
            except Exception as e:
                progress.update(task, description=f"✗ {mode} failed: {e}")

async def demo_cli_tools():
    """Demo CLI tool integrations."""
    console.print("\n[bold cyan]═══ DEMO: CLI Tool Integration ═══[/bold cyan]\n")
    
    tools = [
        ("OpenAI CLI", "openai", "openai api chat.completions.create"),
        ("Claude Desktop", "claude", "claude chat"),
        ("Gemini CLI", "gemini", "gemini prompt"),
        ("Ollama", "ollama", "ollama run llama3.2"),
        ("Hanzo IDE", "~/work/hanzo/ide", "hanzo-ide edit"),
    ]
    
    console.print("Checking available CLI tools:\n")
    
    for name, cmd, example in tools:
        # Check if tool exists
        if cmd.startswith("~"):
            exists = Path(cmd.expanduser()).exists()
        else:
            import shutil
            exists = shutil.which(cmd) is not None
        
        status = "✅" if exists else "❌"
        color = "green" if exists else "red"
        
        console.print(f"{status} [{color}]{name}[/{color}]")
        if exists:
            console.print(f"   Example: [dim]{example}[/dim]")

async def demo_system2_thinking():
    """Demo System 2 thinking with critic agents."""
    console.print("\n[bold cyan]═══ DEMO: System 2 Thinking ═══[/bold cyan]\n")
    
    console.print("System 2 thinking provides deeper analysis:\n")
    
    # Simulate a code review scenario
    code = """def process_data(data):
    result = []
    for item in data:
        if item > 0:
            result.append(item * 2)
    return result"""
    
    console.print("[bold]Original Code:[/bold]")
    console.print(Panel(code, border_style="dim"))
    
    console.print("\n[bold]Critic Agent Analysis:[/bold]")
    
    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console,
    ) as progress:
        task = progress.add_task("Analyzing code...", total=None)
        await asyncio.sleep(2)
        progress.update(task, description="✓ Analysis complete")
    
    critique = """🔍 Code Review:

✅ Strengths:
• Clear function name
• Simple logic
• Returns expected type

⚠️ Improvements:
• Add type hints for clarity
• Consider list comprehension for performance
• Add docstring for documentation
• Handle None/empty inputs

📝 Suggested Refactor:
```python
def process_data(data: list[float]) -> list[float]:
    \"\"\"Process positive numbers by doubling them.\"\"\"
    if not data:
        return []
    return [item * 2 for item in data if item > 0]
```"""
    
    console.print(Panel(critique, title="[bold cyan]Critic Analysis[/bold cyan]",
                       title_align="left", border_style="dim cyan"))

async def demo_cost_optimization():
    """Demo cost-optimized routing."""
    console.print("\n[bold cyan]═══ DEMO: Cost Optimization ═══[/bold cyan]\n")
    
    console.print("Hanzo Dev optimizes costs by routing intelligently:\n")
    
    # Create routing table
    table = Table(title="Intelligent Task Routing", show_header=True,
                  header_style="bold magenta")
    table.add_column("Task Type", style="cyan", width=25)
    table.add_column("Routed To", width=20)
    table.add_column("Cost", style="green")
    table.add_column("Reason", width=35)
    
    routes = [
        ("Simple syntax fix", "Local Llama 3.2", "$0.00", "Basic pattern matching"),
        ("Complex refactoring", "GPT-4", "$0.03", "Requires deep understanding"),
        ("Code review", "Claude 3.5", "$0.02", "Best for analysis"),
        ("Boilerplate generation", "Codestral Free", "$0.00", "Template-based"),
        ("Bug investigation", "GPT-5 Pro", "$0.05", "Critical thinking needed"),
        ("Documentation", "Local Model", "$0.00", "Structured output"),
    ]
    
    for task, model, cost, reason in routes:
        table.add_row(task, model, cost, reason)
    
    console.print(table)
    
    console.print("\n💰 [bold green]Average cost reduction: 90%[/bold green]")
    console.print("   Using local orchestration for routing decisions")

async def demo_mcp_integration():
    """Demo MCP tool integration."""
    console.print("\n[bold cyan]═══ DEMO: MCP Tool Integration ═══[/bold cyan]\n")
    
    console.print("All agents have access to MCP tools:\n")
    
    tools = [
        ("📁 File Operations", "Read, write, edit files"),
        ("🔍 Code Search", "AST-aware search, grep, symbols"),
        ("🌐 Web Fetch", "Browse documentation and APIs"),
        ("💻 Command Execution", "Run tests, build, deploy"),
        ("📊 Data Analysis", "Process CSV, JSON, databases"),
        ("🔄 Git Operations", "Commit, branch, merge"),
        ("📝 Documentation", "Generate docs, comments"),
        ("🧪 Testing", "Run tests, generate test cases"),
    ]
    
    for tool, desc in tools:
        console.print(f"{tool}: [dim]{desc}[/dim]")
    
    console.print("\n[bold]Recursive Agent Calls:[/bold]")
    console.print("• Agents can delegate tasks to each other")
    console.print("• chat_with_<agent> for conversations")
    console.print("• ask_<agent> for questions")
    console.print("• delegate_to_<agent> for task handoff")

async def demo_memory_management():
    """Demo memory and context management."""
    console.print("\n[bold cyan]═══ DEMO: Memory Management ═══[/bold cyan]\n")
    
    console.print("Memory commands (like Claude Desktop):\n")
    
    commands = [
        ("#memory", "Show current memory/context"),
        ("#memory clear", "Clear all memory"),
        ("#memory save", "Save current context"),
        ("#memory load", "Load saved context"),
        ("#memory add <text>", "Add to permanent context"),
        ("#memory remove <id>", "Remove from context"),
    ]
    
    for cmd, desc in commands:
        console.print(f"[cyan]{cmd:20}[/cyan] {desc}")
    
    console.print("\n[bold]Context Window Management:[/bold]")
    console.print("• Automatic summarization for long conversations")
    console.print("• Intelligent context pruning")
    console.print("• Project-specific memory persistence")

async def demo_interactive_session():
    """Demo a real interactive session."""
    console.print("\n[bold cyan]═══ DEMO: Interactive Session ═══[/bold cyan]\n")
    
    # Check for API keys
    has_openai = bool(os.getenv("OPENAI_API_KEY"))
    has_anthropic = bool(os.getenv("ANTHROPIC_API_KEY"))
    
    if not (has_openai or has_anthropic):
        console.print("[yellow]⚠️  No API keys found. Demo will use mock responses.[/yellow]")
        console.print("Set OPENAI_API_KEY or ANTHROPIC_API_KEY for real AI responses.\n")
        return
    
    console.print("[green]✅ API keys found. Starting interactive demo...[/green]\n")
    
    # Create orchestrator
    orchestrator_model = "gpt-4" if has_openai else "claude"
    
    try:
        orchestrator = MultiClaudeOrchestrator(
            workspace_dir="/tmp/hanzo_demo",
            claude_path="claude",
            num_instances=2,
            enable_mcp=True,
            enable_networking=True,
            enable_guardrails=True,
            console=console,
            orchestrator_model=orchestrator_model
        )
        
        repl = HanzoDevREPL(orchestrator)
        
        console.print(f"[bold]Using {orchestrator_model} orchestrator[/bold]\n")
        
        # Demo messages
        test_messages = [
            "What is 2 + 2?",
            "Write a hello world in Python",
            "/help",
        ]
        
        for msg in test_messages:
            console.print(f"\n[dim white]› {msg}[/dim white]")
            
            if msg.startswith("/"):
                # Handle command
                if msg == "/help":
                    console.print("\nAvailable commands:")
                    console.print("  /help     - Show this help")
                    console.print("  /status   - Show system status")
                    console.print("  /clear    - Clear screen")
                    console.print("  /exit     - Exit REPL")
            else:
                # Simulate AI response
                await repl.chat_with_agents(msg)
                
    except Exception as e:
        console.print(f"[red]Error in demo: {e}[/red]")

async def main():
    """Run the complete demo."""
    console.print(Panel.fit(
        "[bold]🚀 Hanzo Dev - AI Coding OS Demo[/bold]\n"
        "Chat-first REPL with Multi-Orchestrator Support",
        border_style="bold cyan"
    ))
    
    demos = [
        ("Chat-First Interface", demo_chat_interface),
        ("Orchestrator Modes", demo_orchestrator_modes),
        ("CLI Tool Integration", demo_cli_tools),
        ("System 2 Thinking", demo_system2_thinking),
        ("Cost Optimization", demo_cost_optimization),
        ("MCP Integration", demo_mcp_integration),
        ("Memory Management", demo_memory_management),
        ("Interactive Session", demo_interactive_session),
    ]
    
    for i, (name, demo_func) in enumerate(demos, 1):
        if i > 1:
            if not Prompt.ask(f"\n[cyan]Continue to {name}?[/cyan]", 
                             default="y", choices=["y", "n"]) == "y":
                break
        
        await demo_func()
    
    console.print("\n" + "="*60)
    console.print(Panel.fit(
        "[bold green]✅ Demo Complete![/bold green]\n\n"
        "To start using Hanzo Dev:\n"
        "[cyan]pip install hanzo==0.3.19[/cyan]\n"
        "[cyan]hanzo dev[/cyan]\n\n"
        "For more info: [link]https://hanzo.ai[/link]",
        border_style="green"
    ))

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        console.print("\n[yellow]Demo interrupted by user[/yellow]")
    except Exception as e:
        console.print(f"\n[red]Demo error: {e}[/red]")
        import traceback
        traceback.print_exc()