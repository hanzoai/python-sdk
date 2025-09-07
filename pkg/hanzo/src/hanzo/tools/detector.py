"""Detect available AI coding tools and assistants."""

import os
import shutil
import subprocess
import httpx
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass

from rich.console import Console
from rich.table import Table
from rich import box


@dataclass
class AITool:
    """Represents an AI coding tool."""
    name: str
    command: str
    display_name: str
    provider: str
    priority: int  # Lower is higher priority
    check_command: Optional[str] = None
    env_var: Optional[str] = None
    api_endpoint: Optional[str] = None
    detected: bool = False
    version: Optional[str] = None
    path: Optional[str] = None


class ToolDetector:
    """Detect and manage available AI coding tools."""
    
    # Define available tools with priority order
    TOOLS = [
        # Hanzo Local Node - highest priority for privacy and local control
        AITool(
            name="hanzod",
            command="hanzo node",
            display_name="Hanzo Node (Local Private AI)",
            provider="hanzo-local",
            priority=0,  # Highest priority - local and private
            check_command=None,  # Check via API endpoint
            api_endpoint="http://localhost:3690/health",
            env_var=None
        ),
        AITool(
            name="hanzo-router",
            command="hanzo router",
            display_name="Hanzo Router (LLM Proxy)",
            provider="hanzo-router",
            priority=1,
            check_command=None,
            api_endpoint="http://localhost:4000/health",
            env_var=None
        ),
        AITool(
            name="claude-code",
            command="claude",
            display_name="Claude Code",
            provider="anthropic",
            priority=2,
            check_command="claude --version",
            env_var="ANTHROPIC_API_KEY"
        ),
        AITool(
            name="hanzo-dev",
            command="hanzo dev",
            display_name="Hanzo Dev (Native)",
            provider="hanzo",
            priority=3,
            check_command="hanzo --version",
            env_var="HANZO_API_KEY"
        ),
        AITool(
            name="openai-codex",
            command="openai",
            display_name="OpenAI Codex",
            provider="openai",
            priority=4,
            check_command="openai --version",
            env_var="OPENAI_API_KEY"
        ),
        AITool(
            name="gemini-cli",
            command="gemini",
            display_name="Gemini CLI",
            provider="google",
            priority=5,
            check_command="gemini --version",
            env_var="GEMINI_API_KEY"
        ),
        AITool(
            name="grok-cli",
            command="grok",
            display_name="Grok CLI",
            provider="xai",
            priority=6,
            check_command="grok --version",
            env_var="GROK_API_KEY"
        ),
        AITool(
            name="openhands",
            command="openhands",
            display_name="OpenHands CLI",
            provider="openhands",
            priority=7,
            check_command="openhands --version",
            env_var=None
        ),
        AITool(
            name="cursor",
            command="cursor",
            display_name="Cursor AI",
            provider="cursor",
            priority=8,
            check_command="cursor --version",
            env_var=None
        ),
        AITool(
            name="codeium",
            command="codeium",
            display_name="Codeium",
            provider="codeium",
            priority=9,
            check_command="codeium --version",
            env_var="CODEIUM_API_KEY"
        ),
        AITool(
            name="aider",
            command="aider",
            display_name="Aider",
            provider="aider",
            priority=10,
            check_command="aider --version",
            env_var=None
        ),
        AITool(
            name="continue",
            command="continue",
            display_name="Continue Dev",
            provider="continue",
            priority=11,
            check_command="continue --version",
            env_var=None
        )
    ]
    
    def __init__(self, console: Optional[Console] = None):
        self.console = console or Console()
        self.detected_tools: List[AITool] = []
        
    def detect_all(self) -> List[AITool]:
        """Detect all available AI tools."""
        self.detected_tools = []
        
        for tool in self.TOOLS:
            if self.detect_tool(tool):
                self.detected_tools.append(tool)
        
        # Sort by priority
        self.detected_tools.sort(key=lambda t: t.priority)
        return self.detected_tools
    
    def detect_tool(self, tool: AITool) -> bool:
        """Detect if a specific tool is available."""
        # Check API endpoint first (for services like hanzod)
        if tool.api_endpoint:
            # For Hanzo Node, directly test the chat endpoint since health may lie
            if tool.name == "hanzod":
                try:
                    # Try both ports in case configuration varies
                    for port in [3690, 8000]:
                        try:
                            # Check if the chat completions endpoint actually works
                            test_response = httpx.post(
                                f"http://localhost:{port}/v1/chat/completions",
                                json={
                                    "messages": [{"role": "user", "content": "test"}],
                                    "model": "default",
                                    "max_tokens": 1
                                },
                                timeout=1.0
                            )
                            # Only accept if we get a proper response (not 404, not connection error)
                            if test_response.status_code in [200, 400, 422]:  # 400/422 means endpoint exists but params wrong
                                tool.detected = True
                                tool.version = f"Running (Port {port})"
                                tool.api_endpoint = f"http://localhost:{port}/health"  # Update port
                                
                                # Try to get model info
                                try:
                                    models_response = httpx.get(f"http://localhost:{port}/v1/models", timeout=0.5)
                                    if models_response.status_code == 200:
                                        models = models_response.json().get("data", [])
                                        if models:
                                            tool.version = f"Running ({len(models)} models, Port {port})"
                                except:
                                    pass
                                
                                return True
                        except (httpx.ConnectError, httpx.TimeoutException):
                            # Connection refused or timeout - node not available on this port
                            continue
                except:
                    pass
                # If we get here, Hanzo Node is not properly available
                return False
            else:
                # For other services, check health endpoint
                try:
                    response = httpx.get(tool.api_endpoint, timeout=1.0)
                    if response.status_code == 200:
                        tool.detected = True
                        tool.version = "Running"
                        return True
                except:
                    pass
        
        # Check if command exists
        if tool.command:
            tool.path = shutil.which(tool.command.split()[0])
            if tool.path:
                tool.detected = True
                
                # Try to get version
                if tool.check_command:
                    try:
                        result = subprocess.run(
                            tool.check_command.split(),
                            capture_output=True,
                            text=True,
                            timeout=2
                        )
                        if result.returncode == 0:
                            tool.version = result.stdout.strip().split()[-1]
                    except:
                        pass
                
                return True
        
        # Check environment variable as fallback
        if tool.env_var and os.getenv(tool.env_var):
            tool.detected = True
            return True
        
        return False
    
    def get_default_tool(self) -> Optional[AITool]:
        """Get the default tool based on priority and availability."""
        if not self.detected_tools:
            self.detect_all()
        
        if self.detected_tools:
            return self.detected_tools[0]
        return None
    
    def get_tool_by_name(self, name: str) -> Optional[AITool]:
        """Get a specific tool by name."""
        for tool in self.TOOLS:
            if tool.name == name or tool.display_name.lower() == name.lower():
                if self.detect_tool(tool):
                    return tool
        return None
    
    def show_available_tools(self):
        """Display available tools in a table."""
        self.detect_all()
        
        table = Table(title="Available AI Coding Tools", box=box.ROUNDED)
        table.add_column("#", style="dim")
        table.add_column("Tool", style="cyan")
        table.add_column("Provider", style="yellow")
        table.add_column("Status", style="green")
        table.add_column("Version", style="blue")
        table.add_column("Priority", style="magenta")
        
        for i, tool in enumerate(self.TOOLS, 1):
            status = "✅ Available" if tool.detected else "❌ Not Found"
            version = tool.version or "Unknown" if tool.detected else "-"
            
            # Highlight the default tool
            if tool.detected and tool == self.detected_tools[0] if self.detected_tools else False:
                table.add_row(
                    str(i),
                    f"[bold green]→ {tool.display_name}[/bold green]",
                    tool.provider,
                    status,
                    version,
                    str(tool.priority)
                )
            else:
                table.add_row(
                    str(i),
                    tool.display_name,
                    tool.provider,
                    status,
                    version,
                    str(tool.priority)
                )
        
        self.console.print(table)
        
        if self.detected_tools:
            default = self.detected_tools[0]
            self.console.print(f"\n[green]Default tool: {default.display_name}[/green]")
            
            # Special message for Hanzo Node
            if default.name == "hanzod":
                self.console.print("[cyan]🔒 Using local private AI - your data stays on your machine[/cyan]")
                self.console.print("[dim]Manage models with: hanzo node models[/dim]")
        else:
            self.console.print("\n[yellow]No AI coding tools detected.[/yellow]")
            self.console.print("[dim]Start Hanzo Node for local AI: hanzo node start[/dim]")
            self.console.print("[dim]Or install Claude Code, OpenAI CLI, etc.[/dim]")
    
    def get_tool_command(self, tool: AITool, prompt: str) -> List[str]:
        """Get the command to execute for a tool with a prompt."""
        if tool.name == "hanzod":
            # Use the local Hanzo node API
            return ["hanzo", "ask", "--local", prompt]
        elif tool.name == "hanzo-router":
            # Use the router proxy
            return ["hanzo", "ask", "--router", prompt]
        elif tool.name == "claude-code":
            return ["claude", prompt]
        elif tool.name == "hanzo-dev":
            return ["hanzo", "dev", "--prompt", prompt]
        elif tool.name == "openai-codex":
            return ["openai", "api", "completions.create", "-m", "code-davinci-002", "-p", prompt]
        elif tool.name == "gemini-cli":
            return ["gemini", "generate", "--prompt", prompt]
        elif tool.name == "grok-cli":
            return ["grok", "complete", prompt]
        elif tool.name == "openhands":
            return ["openhands", "run", prompt]
        elif tool.name == "cursor":
            return ["cursor", "--prompt", prompt]
        elif tool.name == "aider":
            return ["aider", "--message", prompt]
        else:
            return [tool.command, prompt]
    
    def execute_with_tool(self, tool: AITool, prompt: str) -> Tuple[bool, str]:
        """Execute a prompt with a specific tool."""
        try:
            # Special handling for Hanzo services
            if tool.name == "hanzod":
                # Use the local API directly - extract port from the detected endpoint
                try:
                    # Extract port from api_endpoint (e.g., "http://localhost:3690/health")
                    import re
                    port_match = re.search(r':(\d+)', tool.api_endpoint)
                    port = port_match.group(1) if port_match else "3690"
                    
                    response = httpx.post(
                        f"http://localhost:{port}/v1/chat/completions",
                        json={
                            "messages": [{"role": "user", "content": prompt}],
                            "model": "default",  # Use default model
                            "stream": False
                        },
                        timeout=30.0
                    )
                    if response.status_code == 200:
                        result = response.json()
                        return True, result.get("choices", [{}])[0].get("message", {}).get("content", "")
                    else:
                        return False, f"Hanzo Node returned {response.status_code}: {response.text}"
                except Exception as e:
                    return False, f"Hanzo Node error: {e}"
            
            elif tool.name == "hanzo-router":
                # Use the router API
                try:
                    response = httpx.post(
                        "http://localhost:4000/chat/completions",
                        json={
                            "messages": [{"role": "user", "content": prompt}],
                            "model": "gpt-3.5-turbo",  # Router will route to best available
                            "stream": False
                        },
                        timeout=30.0
                    )
                    if response.status_code == 200:
                        result = response.json()
                        return True, result.get("choices", [{}])[0].get("message", {}).get("content", "")
                except Exception as e:
                    return False, f"Router error: {e}"
            
            # Default command execution
            command = self.get_tool_command(tool, prompt)
            result = subprocess.run(
                command,
                capture_output=True,
                text=True,
                timeout=30
            )
            
            if result.returncode == 0:
                return True, result.stdout
            else:
                return False, result.stderr or "Command failed"
        except subprocess.TimeoutExpired:
            return False, "Command timed out"
        except Exception as e:
            return False, str(e)
    
    def execute_with_fallback(self, prompt: str) -> Tuple[bool, str, AITool]:
        """Execute with fallback through available tools."""
        if not self.detected_tools:
            self.detect_all()
        
        for tool in self.detected_tools:
            self.console.print(f"[dim]Trying {tool.display_name}...[/dim]")
            success, output = self.execute_with_tool(tool, prompt)
            
            if success:
                return True, output, tool
            else:
                self.console.print(f"[yellow]{tool.display_name} failed: {output}[/yellow]")
        
        return False, "No available tools could handle the request", None