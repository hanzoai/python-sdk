"""IPython-based REPL for intimate Hanzo MCP interaction."""

import asyncio
import inspect
import os
import sys
from typing import Any, Dict, Optional

from IPython import get_ipython
from IPython.terminal.embed import InteractiveShellEmbed
from IPython.core.magic import Magics, line_magic, cell_magic, magics_class
from rich.console import Console
from rich.markdown import Markdown
from rich.syntax import Syntax

from hanzo_mcp.server import HanzoMCPServer
from hanzo_mcp.tools import *  # Import all tools for direct access
from .llm_client import LLMClient
from .tool_executor import ToolExecutor


@magics_class
class HanzoMagics(Magics):
    """Custom magic commands for Hanzo REPL."""
    
    def __init__(self, shell, repl):
        super().__init__(shell)
        self.repl = repl
        self.console = Console()
    
    @line_magic
    def chat(self, line):
        """Chat with AI: %chat <message>"""
        if not line:
            print("Usage: %chat <message>")
            return
        
        # Run async chat in sync context
        loop = asyncio.get_event_loop()
        response = loop.run_until_complete(self.repl.tool_executor.execute_with_tools(line))
        self.console.print(Markdown(response))
    
    @cell_magic
    def ai(self, line, cell):
        """Multi-line AI chat."""
        message = cell.strip()
        if not message:
            print("Please provide a message in the cell")
            return
        
        loop = asyncio.get_event_loop()
        response = loop.run_until_complete(self.repl.tool_executor.execute_with_tools(message))
        self.console.print(Markdown(response))
    
    @line_magic
    def tools(self, line):
        """List available MCP tools."""
        self.repl.list_tools()
    
    @line_magic
    def tool(self, line):
        """Execute a tool: %tool <tool_name> <json_args>"""
        parts = line.split(maxsplit=1)
        if len(parts) < 2:
            print("Usage: %tool <tool_name> <json_args>")
            return
        
        tool_name = parts[0]
        try:
            import json
            args = json.loads(parts[1])
        except:
            print("Invalid JSON arguments")
            return
        
        loop = asyncio.get_event_loop()
        result = loop.run_until_complete(self.repl.execute_tool(tool_name, args))
        print(result)
    
    @line_magic
    def edit_self(self, line):
        """Edit the REPL source code: %edit_self <file>"""
        if not line:
            line = "ipython_repl.py"
        
        file_path = os.path.join(os.path.dirname(__file__), line)
        if os.path.exists(file_path):
            # Use IPython's editor
            get_ipython().magic(f'edit {file_path}')
            
            # Reload the module
            import importlib
            module_name = f"hanzo_repl.{line.replace('.py', '')}"
            if module_name in sys.modules:
                importlib.reload(sys.modules[module_name])
                print(f"Reloaded {module_name}")
        else:
            print(f"File not found: {file_path}")
    
    @line_magic
    def model(self, line):
        """Set or show LLM model: %model [model_name]"""
        if not line:
            info = self.repl.llm_client.get_model_info()
            print(f"Current model: {info['model']}")
            print(f"Provider: {info['provider']}")
        else:
            try:
                self.repl.llm_client.set_model(line)
                print(f"Model set to: {line}")
            except Exception as e:
                print(f"Error: {e}")


class HanzoIPythonREPL:
    """IPython-based REPL with direct MCP access."""
    
    def __init__(self):
        self.console = Console()
        self.mcp_server = None
        self.llm_client = None
        self.tool_executor = None
        self.tools = {}  # Direct tool access
        
    async def initialize(self):
        """Initialize MCP and LLM components."""
        # Initialize MCP server
        self.mcp_server = HanzoMCPServer()
        await self.mcp_server.initialize()
        
        # Make tools directly accessible
        self.tools = self.mcp_server.tools
        
        # Initialize LLM client
        self.llm_client = LLMClient()
        if not self.llm_client.get_available_providers():
            self.console.print("[red]No LLM providers available![/red]")
            self.console.print("Set OPENAI_API_KEY, ANTHROPIC_API_KEY, or other provider keys")
            sys.exit(1)
        
        # Initialize tool executor
        self.tool_executor = ToolExecutor(self.mcp_server, self.llm_client)
    
    def list_tools(self):
        """List available tools with their methods."""
        for name, tool in sorted(self.tools.items()):
            print(f"\n[{name}] - {tool.description}")
            
            # Show available methods
            methods = [m for m in dir(tool) if not m.startswith('_') and callable(getattr(tool, m))]
            for method in methods:
                if method not in ['execute', 'get_schema']:
                    print(f"  .{method}()")
    
    async def execute_tool(self, tool_name: str, args: Dict[str, Any]) -> Any:
        """Execute a tool by name."""
        if tool_name not in self.tools:
            raise ValueError(f"Unknown tool: {tool_name}")
        
        tool = self.tools[tool_name]
        return await tool.execute(**args)
    
    def create_namespace(self) -> Dict[str, Any]:
        """Create the namespace for IPython shell."""
        namespace = {
            # REPL instance
            'repl': self,
            'mcp': self.mcp_server,
            'llm': self.llm_client,
            'executor': self.tool_executor,
            
            # Direct tool access
            'tools': self.tools,
            
            # Convenience functions
            'chat': self._chat_sync,
            'execute': self._execute_sync,
            'list_tools': self.list_tools,
            
            # Console for rich output
            'console': self.console,
            'print_md': lambda x: self.console.print(Markdown(x)),
            'print_code': lambda x, lang='python': self.console.print(Syntax(x, lang)),
        }
        
        # Add individual tools to namespace
        for name, tool in self.tools.items():
            # Create a wrapper that handles async
            namespace[name] = self._create_tool_wrapper(tool)
        
        return namespace
    
    def _create_tool_wrapper(self, tool):
        """Create a sync wrapper for async tool."""
        def wrapper(**kwargs):
            loop = asyncio.get_event_loop()
            return loop.run_until_complete(tool.execute(**kwargs))
        
        wrapper.__doc__ = tool.description
        wrapper.tool = tool  # Keep reference to original tool
        return wrapper
    
    def _chat_sync(self, message: str) -> str:
        """Synchronous chat wrapper."""
        loop = asyncio.get_event_loop()
        response = loop.run_until_complete(self.tool_executor.execute_with_tools(message))
        self.console.print(Markdown(response))
        return response
    
    def _execute_sync(self, tool_name: str, **kwargs) -> Any:
        """Synchronous tool execution wrapper."""
        loop = asyncio.get_event_loop()
        return loop.run_until_complete(self.execute_tool(tool_name, kwargs))
    
    def run(self):
        """Run the IPython REPL."""
        # Initialize asyncio in the current thread
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        # Initialize components
        loop.run_until_complete(self.initialize())
        
        # Create IPython shell
        namespace = self.create_namespace()
        
        # Configure IPython
        config = {
            'TerminalInteractiveShell': {
                'colors': 'Linux',
                'automagic': True,
                'banner1': self._get_banner(),
                'banner2': '',
            }
        }
        
        shell = InteractiveShellEmbed(
            config=config,
            user_ns=namespace,
            exit_msg="Goodbye!"
        )
        
        # Register magic commands
        shell.register_magics(HanzoMagics(shell, self))
        
        # Add some helpful aliases
        shell.alias_manager.define_alias('ls', 'ls -la')
        shell.alias_manager.define_alias('ll', 'ls -la')
        
        # Print welcome info
        self.console.print(f"[green]Model: {self.llm_client.current_model}[/green]")
        self.console.print("[dim]Type ? for help, ?? for more details[/dim]")
        self.console.print("[dim]Use %chat for AI chat, tools.<tab> for completion[/dim]")
        
        # Start the shell
        shell()
    
    def _get_banner(self) -> str:
        """Get the REPL banner."""
        return """
[bold cyan]Hanzo REPL[/bold cyan] - Direct access to Model Context Protocol tools
        
Available objects:
  • mcp         - MCP server instance
  • tools       - Direct tool access (tools.read_file, tools.run_command, etc.)
  • chat(msg)   - Chat with AI using MCP tools
  • execute()   - Execute a tool by name
  
Magic commands:
  • %chat       - Single-line AI chat
  • %%ai        - Multi-line AI chat
  • %tools      - List available tools
  • %tool       - Execute a specific tool
  • %edit_self  - Edit REPL source code
  • %model      - Set/show LLM model
  
Examples:
  >>> read_file(file_path="/etc/hosts")
  >>> chat("What files are in the current directory?")
  >>> tools.search(query="def main", path=".")
  >>> %chat explain what this code does
"""


def main():
    """Main entry point for IPython REPL."""
    repl = HanzoIPythonREPL()
    repl.run()


if __name__ == "__main__":
    main()