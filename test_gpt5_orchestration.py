#!/usr/bin/env python3
"""
Test GPT-5/Codex as orchestrator for comprehensive code review.

This script demonstrates using the most powerful models (GPT-5, GPT-4, Codex)
as orchestrators to review all code and provide system-level improvements.
"""

import asyncio
import json
import os
import subprocess
import sys
from pathlib import Path
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.syntax import Syntax

console = Console()

class GPT5CodeReviewer:
    """Use GPT-5/Codex for comprehensive code review and orchestration."""
    
    def __init__(self, model="gpt-5", api_key=None):
        """Initialize with specified model.
        
        Args:
            model: Model to use (gpt-5, gpt-4o, gpt-4-turbo, codex, o3)
            api_key: OpenAI API key (reads from env if not provided)
        """
        self.model = model
        self.api_key = api_key or os.getenv("OPENAI_API_KEY")
        
        # Model configurations for different review scenarios
        self.model_configs = {
            "gpt-5": {
                "name": "gpt-5-latest",
                "context": 128000,
                "capabilities": ["code_review", "architecture", "security", "performance"],
                "cost_per_1k": 0.15
            },
            "gpt-4o": {
                "name": "gpt-4o",  
                "context": 128000,
                "capabilities": ["code_review", "architecture", "refactoring"],
                "cost_per_1k": 0.05
            },
            "gpt-4-turbo": {
                "name": "gpt-4-turbo-preview",
                "context": 128000,
                "capabilities": ["code_review", "documentation"],
                "cost_per_1k": 0.03
            },
            "codex": {
                "name": "code-davinci-002",
                "context": 8000,
                "capabilities": ["code_generation", "completion", "review"],
                "cost_per_1k": 0.02
            },
            "o3": {
                "name": "o3-preview",
                "context": 200000,
                "capabilities": ["reasoning", "architecture", "security", "optimization"],
                "cost_per_1k": 0.20
            }
        }
    
    async def review_with_hanzo_dev(self, project_path: Path):
        """Use hanzo dev with GPT-5 orchestrator to review entire project."""
        
        console.print(Panel.fit(
            f"[bold cyan]Code Review with {self.model.upper()} Orchestrator[/bold cyan]\n"
            f"Project: {project_path}",
            title="🤖 AI Code Review"
        ))
        
        # Start hanzo dev with GPT-5 orchestrator
        cmd = [
            "hanzo", "dev",
            "--orchestrator", self.model,
            "--instances", "3",  # Main coder + 2 reviewers
            "--critic-instances", "2",  # 2 critic agents
            "--enable-guardrails",
            "--workspace", str(project_path),
            "--review-mode"  # Special mode for code review
        ]
        
        console.print(f"[yellow]Starting:[/yellow] {' '.join(cmd)}")
        
        # Create review prompts for different aspects
        review_tasks = [
            {
                "aspect": "Security",
                "prompt": "Review the codebase for security vulnerabilities, focusing on:\n"
                         "- Input validation\n- Authentication/authorization\n"
                         "- Data sanitization\n- Secret management\n"
                         "- Dependency vulnerabilities"
            },
            {
                "aspect": "Performance", 
                "prompt": "Analyze performance bottlenecks and optimization opportunities:\n"
                         "- Algorithm complexity\n- Database queries\n"
                         "- Caching strategies\n- Async/parallel processing\n"
                         "- Memory usage patterns"
            },
            {
                "aspect": "Architecture",
                "prompt": "Evaluate the system architecture and design patterns:\n"
                         "- SOLID principles adherence\n- Coupling and cohesion\n"
                         "- Scalability considerations\n- Design pattern usage\n"
                         "- Module boundaries and interfaces"
            },
            {
                "aspect": "Code Quality",
                "prompt": "Assess overall code quality and maintainability:\n"
                         "- Code duplication\n- Naming conventions\n"
                         "- Documentation completeness\n- Test coverage\n"
                         "- Error handling patterns"
            },
            {
                "aspect": "Best Practices",
                "prompt": "Check adherence to language-specific best practices:\n"
                         "- Python: PEP 8, type hints, docstrings\n"
                         "- JavaScript: ESLint rules, modern syntax\n"
                         "- Error handling and logging\n- Configuration management"
            }
        ]
        
        # Display review plan
        table = Table(title="Review Plan", show_header=True)
        table.add_column("Aspect", style="cyan")
        table.add_column("Focus Areas", style="white")
        
        for task in review_tasks:
            table.add_row(
                task["aspect"],
                task["prompt"].replace("\n", " ").replace("- ", "• ")[:80] + "..."
            )
        
        console.print(table)
        
        # Execute reviews
        results = {}
        for task in review_tasks:
            console.print(f"\n[bold]Reviewing: {task['aspect']}[/bold]")
            
            # Simulate review execution (in real implementation, this would
            # call hanzo dev with the specific review prompt)
            result = await self._execute_review(task["aspect"], task["prompt"])
            results[task["aspect"]] = result
            
            # Display summary
            if result.get("issues"):
                console.print(f"  [red]✗ Found {len(result['issues'])} issues[/red]")
            else:
                console.print(f"  [green]✓ No major issues found[/green]")
            
            if result.get("suggestions"):
                console.print(f"  [yellow]💡 {len(result['suggestions'])} suggestions[/yellow]")
        
        return results
    
    async def _execute_review(self, aspect: str, prompt: str):
        """Execute a specific review aspect."""
        
        # In a real implementation, this would:
        # 1. Send the prompt to hanzo dev
        # 2. Wait for orchestrator to coordinate agents
        # 3. Collect and format results
        
        # For demonstration, return sample results
        return {
            "aspect": aspect,
            "status": "completed",
            "issues": [],
            "suggestions": [
                f"Consider improving {aspect.lower()} in module X",
                f"Optimize {aspect.lower()} patterns in service Y"
            ],
            "score": 85
        }
    
    def generate_review_report(self, results: dict):
        """Generate comprehensive review report."""
        
        console.print("\n" + "="*60)
        console.print(Panel.fit(
            "[bold green]Code Review Complete[/bold green]",
            title="📊 Summary Report"
        ))
        
        # Overall score calculation
        total_score = sum(r.get("score", 0) for r in results.values())
        avg_score = total_score / len(results) if results else 0
        
        # Score interpretation
        if avg_score >= 90:
            grade = "A"
            color = "green"
            message = "Excellent code quality!"
        elif avg_score >= 80:
            grade = "B"
            color = "yellow"
            message = "Good quality with minor improvements needed"
        elif avg_score >= 70:
            grade = "C"
            color = "orange"
            message = "Acceptable but needs attention"
        else:
            grade = "D"
            color = "red"
            message = "Significant improvements required"
        
        console.print(f"\n[bold]Overall Grade:[/bold] [{color}]{grade}[/{color}] ({avg_score:.1f}/100)")
        console.print(f"[italic]{message}[/italic]\n")
        
        # Detailed results
        for aspect, result in results.items():
            console.print(f"[bold cyan]{aspect}:[/bold cyan]")
            console.print(f"  Score: {result.get('score', 0)}/100")
            
            if result.get("issues"):
                console.print("  [red]Issues:[/red]")
                for issue in result["issues"][:3]:
                    console.print(f"    • {issue}")
            
            if result.get("suggestions"):
                console.print("  [yellow]Suggestions:[/yellow]")
                for suggestion in result["suggestions"][:3]:
                    console.print(f"    • {suggestion}")
            
            console.print()


async def main():
    """Run GPT-5 code review demonstration."""
    
    # Display available models
    console.print(Panel.fit(
        "[bold]Available Orchestrator Models[/bold]\n\n"
        "• [cyan]gpt-5[/cyan] - Most advanced, best for complex reviews\n"
        "• [cyan]gpt-4o[/cyan] - Optimized GPT-4, good balance\n"
        "• [cyan]gpt-4-turbo[/cyan] - Fast GPT-4 variant\n"
        "• [cyan]codex[/cyan] - Specialized for code\n"
        "• [cyan]o3[/cyan] - Advanced reasoning model\n",
        title="🎯 Model Selection"
    ))
    
    # Example: Review current project with GPT-5
    reviewer = GPT5CodeReviewer(model="gpt-5")
    project_path = Path.cwd()
    
    console.print("\n[bold]Starting comprehensive code review...[/bold]\n")
    
    # Run the review
    results = await reviewer.review_with_hanzo_dev(project_path)
    
    # Generate report
    reviewer.generate_review_report(results)
    
    # Show example commands
    console.print("\n" + "="*60)
    console.print(Panel.fit(
        "[bold]Example Commands[/bold]\n\n"
        "[cyan]# Use GPT-5 as orchestrator[/cyan]\n"
        "hanzo dev --orchestrator gpt-5\n\n"
        
        "[cyan]# Use GPT-4o for balanced performance[/cyan]\n"
        "hanzo dev --orchestrator gpt-4o --instances 3\n\n"
        
        "[cyan]# Use Codex for code-specific tasks[/cyan]\n"
        "hanzo dev --orchestrator codex --focus code-generation\n\n"
        
        "[cyan]# Use O3 for complex reasoning[/cyan]\n"
        "hanzo dev --orchestrator o3 --enable-reasoning\n\n"
        
        "[cyan]# Hybrid: Local for simple, GPT-5 for complex[/cyan]\n"
        "hanzo dev --orchestrator gpt-5 --use-hanzo-net\n",
        title="💡 Usage Examples"
    ))


if __name__ == "__main__":
    asyncio.run(main())