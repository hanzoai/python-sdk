#!/usr/bin/env python3
"""
Demo: GPT-5 Pro via Codex Configuration

This demonstrates the ultimate code development setup:
- GPT-5 Pro for high-level orchestration and reasoning
- Codex for specialized code generation and completion
- Hanzo router for unified LLM access
- Cost optimization with intelligent routing
"""

import os
import asyncio

from rich.panel import Panel
from rich.table import Table
from rich.syntax import Syntax
from rich.console import Console

console = Console()

# Example configurations
CONFIGS = {
    "gpt-5-pro-codex": {
        "description": "GPT-5 Pro + Codex hybrid for ultimate code development",
        "command": "hanzo dev --orchestrator gpt-5-pro-codex",
        "features": [
            "GPT-5 Pro for architecture and complex reasoning",
            "Codex for code generation and completion",
            "Automatic task routing based on complexity",
            "Full MCP tool support",
            "Cost-optimized with intelligent routing",
        ],
    },
    "router-gpt5": {
        "description": "GPT-5 via hanzo-router for unified access",
        "command": "hanzo dev --orchestrator router:gpt-5",
        "features": [
            "Access GPT-5 through hanzo-router",
            "Automatic fallback to other models",
            "Load balancing across endpoints",
            "Response caching for efficiency",
            "Unified billing and monitoring",
        ],
    },
    "direct-codex": {
        "description": "Direct Codex access for pure code tasks",
        "command": "hanzo dev --orchestrator codex",
        "features": [
            "Direct OpenAI Codex API access",
            "Optimized for code generation",
            "Support for multiple languages",
            "Auto-completion and refactoring",
            "Docstring and comment generation",
        ],
    },
    "hybrid-optimized": {
        "description": "Hybrid mode with router + direct access",
        "command": "hanzo dev --orchestrator-mode hybrid --router-endpoint http://localhost:4000",
        "features": [
            "Use router for most models",
            "Direct access for specialized models",
            "Fallback mechanisms",
            "Cost tracking across all providers",
            "Intelligent routing decisions",
        ],
    },
}


def display_configuration_options():
    """Display available orchestrator configurations."""

    console.print(
        Panel.fit(
            "[bold cyan]Hanzo Dev - Orchestrator Configurations[/bold cyan]\n\n"
            "Choose your orchestration strategy:",
            title="🎯 Configuration Options",
        )
    )

    for name, config in CONFIGS.items():
        console.print(f"\n[bold yellow]{name}[/bold yellow]")
        console.print(f"  {config['description']}")
        console.print(f"  [dim]Command:[/dim] [cyan]{config['command']}[/cyan]")
        console.print("  [dim]Features:[/dim]")
        for feature in config["features"]:
            console.print(f"    • {feature}")


def show_routing_logic():
    """Show how tasks are routed to different models."""

    console.print("\n" + "=" * 60)
    console.print(
        Panel.fit("[bold]Intelligent Task Routing[/bold]", title="🧠 Routing Logic")
    )

    table = Table(show_header=True, header_style="bold cyan")
    table.add_column("Task Type", style="yellow")
    table.add_column("Routed To", style="green")
    table.add_column("Reason", style="white")
    table.add_column("Cost", style="cyan")

    routing_rules = [
        ("Architecture Design", "GPT-5 Pro", "Complex reasoning required", "$$$"),
        ("Code Generation", "Codex", "Specialized for code", "$"),
        ("Bug Fixing", "GPT-4o", "Good balance of capability/cost", "$$"),
        ("Code Formatting", "Local Model", "Simple mechanical task", "Free"),
        ("Security Analysis", "GPT-5 Pro", "Critical analysis needed", "$$$"),
        ("Documentation", "GPT-4-turbo", "Fast and capable", "$$"),
        ("Syntax Checking", "Local Model", "Rule-based task", "Free"),
        ("Refactoring", "Codex + GPT-4o", "Code understanding + validation", "$$"),
        ("Test Generation", "Codex", "Code generation specialist", "$"),
        ("Code Review", "GPT-5 Pro + Critics", "Comprehensive analysis", "$$$"),
    ]

    for task, model, reason, cost in routing_rules:
        table.add_row(task, model, reason, cost)

    console.print(table)


def show_example_workflow():
    """Show an example development workflow."""

    console.print("\n" + "=" * 60)
    console.print(
        Panel.fit(
            "[bold]Example Workflow: Building a REST API[/bold]",
            title="📝 Development Flow",
        )
    )

    workflow_steps = [
        {
            "step": "1. Architecture Planning",
            "orchestrator": "GPT-5 Pro",
            "action": "Design API structure, define endpoints, plan data models",
            "code": None,
        },
        {
            "step": "2. Code Generation",
            "orchestrator": "Codex",
            "action": "Generate FastAPI boilerplate, models, and routes",
            "code": """from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import List, Optional

app = FastAPI(title="Example API")

class Item(BaseModel):
    id: int
    name: str
    description: Optional[str] = None
    price: float

@app.get("/items/{item_id}")
async def get_item(item_id: int):
    # Generated by Codex
    return {"item_id": item_id}""",
        },
        {
            "step": "3. Implementation Review",
            "orchestrator": "GPT-4o (Critic)",
            "action": "Review generated code for best practices",
            "code": None,
        },
        {
            "step": "4. Security Audit",
            "orchestrator": "GPT-5 Pro",
            "action": "Analyze for vulnerabilities, suggest improvements",
            "code": None,
        },
        {
            "step": "5. Test Generation",
            "orchestrator": "Codex",
            "action": "Generate comprehensive test suite",
            "code": """import pytest
from fastapi.testclient import TestClient

def test_get_item():
    # Generated test by Codex
    response = client.get("/items/1")
    assert response.status_code == 200""",
        },
        {
            "step": "6. Documentation",
            "orchestrator": "GPT-4-turbo",
            "action": "Generate API documentation and README",
            "code": None,
        },
    ]

    for step_info in workflow_steps:
        console.print(f"\n[bold cyan]{step_info['step']}[/bold cyan]")
        console.print(f"  [yellow]Orchestrator:[/yellow] {step_info['orchestrator']}")
        console.print(f"  [dim]Action:[/dim] {step_info['action']}")

        if step_info["code"]:
            console.print("  [dim]Generated Code:[/dim]")
            syntax = Syntax(
                step_info["code"], "python", theme="monokai", line_numbers=False
            )
            console.print(syntax)


def show_cost_comparison():
    """Show cost comparison between different configurations."""

    console.print("\n" + "=" * 60)
    console.print(Panel.fit("[bold]Cost Analysis[/bold]", title="💰 Cost Comparison"))

    table = Table(show_header=True, header_style="bold cyan")
    table.add_column("Configuration", style="yellow")
    table.add_column("Hourly Cost", style="green", justify="right")
    table.add_column("Daily Cost", style="green", justify="right")
    table.add_column("Savings vs Pure GPT-5", style="cyan", justify="right")

    costs = [
        ("Pure GPT-5", "$12.00", "$288.00", "0%"),
        ("GPT-5 Pro + Codex", "$8.50", "$204.00", "29%"),
        ("Router-based Mixed", "$6.00", "$144.00", "50%"),
        ("Hybrid Optimized", "$3.50", "$84.00", "71%"),
        ("Cost-Optimized (Local+API)", "$1.20", "$28.80", "90%"),
        ("Pure Local Models", "$0.00", "$0.00", "100%"),
    ]

    for config, hourly, daily, savings in costs:
        table.add_row(config, hourly, daily, savings)

    console.print(table)

    console.print(
        "\n[yellow]Note:[/yellow] Costs are estimates based on typical usage patterns"
    )
    console.print("Actual costs depend on task complexity and token usage")


def main():
    """Run the demo."""

    console.print("╔" + "═" * 58 + "╗")
    console.print(
        "║  [bold cyan]Hanzo Dev - GPT-5 Pro via Codex Demo[/bold cyan]"
        + " " * 18
        + "║"
    )
    console.print("╚" + "═" * 58 + "╝\n")

    # Show configuration options
    display_configuration_options()

    # Show routing logic
    show_routing_logic()

    # Show example workflow
    show_example_workflow()

    # Show cost comparison
    show_cost_comparison()

    # Show how to get started
    console.print("\n" + "=" * 60)
    console.print(
        Panel.fit(
            "[bold green]Getting Started[/bold green]\n\n"
            "1. Start hanzo-router (if using router mode):\n"
            "   [cyan]hanzo router start[/cyan]\n\n"
            "2. Set your API keys:\n"
            "   [cyan]export OPENAI_API_KEY=sk-...[/cyan]\n"
            "   [cyan]export ANTHROPIC_API_KEY=sk-ant-...[/cyan]\n\n"
            "3. Run with GPT-5 Pro + Codex:\n"
            "   [cyan]hanzo dev --orchestrator gpt-5-pro-codex[/cyan]\n\n"
            "4. Or use router mode:\n"
            "   [cyan]hanzo dev --orchestrator router:gpt-5[/cyan]\n\n"
            "5. Or direct Codex mode:\n"
            "   [cyan]hanzo dev --orchestrator codex[/cyan]\n\n"
            "For more options: [cyan]hanzo dev --help[/cyan]",
            title="🚀 Quick Start",
        )
    )


if __name__ == "__main__":
    main()
