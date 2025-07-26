"""Backend implementations for different AI CLI tools."""

import asyncio
import json
import os
import subprocess
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Any, Dict, List, Optional

from rich.console import Console
from rich.markdown import Markdown


class Backend(ABC):
    """Abstract base class for AI backends."""
    
    @abstractmethod
    async def chat(self, message: str, tools: Optional[List[Dict]] = None) -> str:
        """Send a chat message and get response."""
        pass
    
    @abstractmethod
    def get_config_file(self) -> str:
        """Get the configuration file name for this backend."""
        pass
    
    @abstractmethod
    def is_available(self) -> bool:
        """Check if this backend is available."""
        pass


class ClaudeCodeBackend(Backend):
    """Claude Code CLI backend with personal account support."""
    
    def __init__(self):
        self.cli_path = self._find_claude_code()
        self.authenticated = False
        
    def _find_claude_code(self) -> Optional[str]:
        """Find Claude Code CLI executable."""
        # Check common locations
        paths = [
            "claude",  # In PATH
            "/usr/local/bin/claude",
            "/opt/homebrew/bin/claude",
            os.path.expanduser("~/.local/bin/claude"),
        ]
        
        for path in paths:
            try:
                result = subprocess.run([path, "--version"], capture_output=True, text=True)
                if result.returncode == 0:
                    return path
            except FileNotFoundError:
                continue
                
        return None
    
    def is_available(self) -> bool:
        """Check if Claude Code is available."""
        if self.cli_path is None:
            return False
            
        # Check if already authenticated
        self.authenticated = self._check_auth()
        return True
    
    def _check_auth(self) -> bool:
        """Check if Claude Code is authenticated."""
        if not self.cli_path:
            return False
            
        try:
            # Claude Code should have an auth status command
            result = subprocess.run(
                [self.cli_path, "auth", "status"],
                capture_output=True,
                text=True
            )
            
            # Check if authenticated (Claude Code should indicate this)
            return result.returncode == 0 and "authenticated" in result.stdout.lower()
            
        except Exception:
            return False
    
    async def authenticate(self) -> bool:
        """Authenticate with Claude using personal account."""
        if not self.cli_path:
            raise RuntimeError("Claude Code CLI not found")
        
        console = Console()
        console.print("[yellow]Opening browser for Claude authentication...[/yellow]")
        
        # Claude Code auth login command
        proc = await asyncio.create_subprocess_exec(
            self.cli_path, "auth", "login",
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        
        stdout, stderr = await proc.communicate()
        
        if proc.returncode == 0:
            console.print("[green]Successfully authenticated with Claude![/green]")
            self.authenticated = True
            return True
        else:
            console.print(f"[red]Authentication failed: {stderr.decode()}[/red]")
            return False
    
    def get_config_file(self) -> str:
        """Get config file for Claude Code."""
        return "CLAUDE.md"
    
    async def chat(self, message: str, tools: Optional[List[Dict]] = None) -> str:
        """Send message to Claude Code."""
        if not self.cli_path:
            raise RuntimeError("Claude Code CLI not found")
        
        # Check authentication
        if not self.authenticated and not self._check_auth():
            console = Console()
            console.print("[yellow]Not authenticated with Claude. Attempting login...[/yellow]")
            if not await self.authenticate():
                raise RuntimeError("Failed to authenticate with Claude")
        
        # Prepare command - Claude Code uses simple message format when authenticated
        cmd = [self.cli_path, message]
        
        # Add any additional flags for MCP tools if needed
        if tools:
            # Claude Code might handle tools differently when using personal account
            # May need to use --mcp flag or similar
            cmd.insert(1, "--with-tools")
        
        # Run command
        proc = await asyncio.create_subprocess_exec(
            *cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
            stdin=asyncio.subprocess.PIPE  # For interactive mode if needed
        )
        
        stdout, stderr = await proc.communicate()
        
        if proc.returncode != 0:
            # Check if it's an auth error
            if "unauthorized" in stderr.decode().lower() or "auth" in stderr.decode().lower():
                self.authenticated = False
                raise RuntimeError("Claude authentication expired. Please re-authenticate.")
            raise RuntimeError(f"Claude Code error: {stderr.decode()}")
        
        return stdout.decode()
    
    async def logout(self) -> None:
        """Logout from Claude account."""
        if self.cli_path:
            proc = await asyncio.create_subprocess_exec(
                self.cli_path, "auth", "logout",
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            await proc.communicate()
            self.authenticated = False


class OpenAICodexBackend(Backend):
    """OpenAI Codex/GPT CLI backend."""
    
    def __init__(self):
        self.cli_path = self._find_openai_cli()
        
    def _find_openai_cli(self) -> Optional[str]:
        """Find OpenAI CLI executable."""
        paths = [
            "openai",  # In PATH
            "gpt",      # Alternative name
            "/usr/local/bin/openai",
            os.path.expanduser("~/.local/bin/openai"),
        ]
        
        for path in paths:
            try:
                result = subprocess.run([path, "--version"], capture_output=True, text=True)
                if result.returncode == 0:
                    return path
            except FileNotFoundError:
                continue
                
        return None
    
    def is_available(self) -> bool:
        """Check if OpenAI CLI is available."""
        return self.cli_path is not None or os.getenv("OPENAI_API_KEY")
    
    def get_config_file(self) -> str:
        """Get config file for OpenAI."""
        return "AGENTS.md"
    
    async def chat(self, message: str, tools: Optional[List[Dict]] = None) -> str:
        """Send message to OpenAI."""
        if self.cli_path:
            # Use CLI
            cmd = [self.cli_path, "api", "chat.completions.create"]
            
            # Build request
            request = {
                "model": "gpt-4-turbo-preview",
                "messages": [{"role": "user", "content": message}]
            }
            
            if tools:
                request["tools"] = tools
                request["tool_choice"] = "auto"
            
            cmd.extend(["-g", json.dumps(request)])
            
            proc = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            
            stdout, stderr = await proc.communicate()
            
            if proc.returncode != 0:
                raise RuntimeError(f"OpenAI CLI error: {stderr.decode()}")
            
            # Parse response
            response = json.loads(stdout.decode())
            return response["choices"][0]["message"]["content"]
            
        else:
            # Use API directly
            import openai
            
            client = openai.AsyncOpenAI()
            
            messages = [{"role": "user", "content": message}]
            
            if tools:
                response = await client.chat.completions.create(
                    model="gpt-4-turbo-preview",
                    messages=messages,
                    tools=tools,
                    tool_choice="auto"
                )
            else:
                response = await client.chat.completions.create(
                    model="gpt-4-turbo-preview",
                    messages=messages
                )
            
            return response.choices[0].message.content


class HanzoDevBackend(Backend):
    """Hanzo Dev AI backend."""
    
    def __init__(self):
        self.cli_path = self._find_hanzo_dev()
        
    def _find_hanzo_dev(self) -> Optional[str]:
        """Find hanzo-dev executable."""
        paths = [
            "hanzo-dev",
            "/usr/local/bin/hanzo-dev",
            os.path.expanduser("~/.local/bin/hanzo-dev"),
            # Check in parent directory
            os.path.join(os.path.dirname(os.path.dirname(__file__)), "..", "dev", "hanzo-dev"),
        ]
        
        for path in paths:
            if os.path.exists(path) and os.access(path, os.X_OK):
                return path
                
        return None
    
    def is_available(self) -> bool:
        """Check if hanzo-dev is available."""
        return self.cli_path is not None
    
    def get_config_file(self) -> str:
        """Get config file for hanzo-dev."""
        return "LLM.md"
    
    async def chat(self, message: str, tools: Optional[List[Dict]] = None) -> str:
        """Send message to hanzo-dev."""
        if not self.cli_path:
            raise RuntimeError("hanzo-dev not found")
        
        cmd = [self.cli_path, "chat", "--message", message]
        
        if tools:
            cmd.extend(["--tools", json.dumps(tools)])
        
        proc = await asyncio.create_subprocess_exec(
            *cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        
        stdout, stderr = await proc.communicate()
        
        if proc.returncode != 0:
            raise RuntimeError(f"hanzo-dev error: {stderr.decode()}")
        
        return stdout.decode()


class EmbeddedBackend(Backend):
    """Embedded LLM backend using litellm."""
    
    def __init__(self, llm_client):
        self.llm_client = llm_client
        
    def is_available(self) -> bool:
        """Check if embedded backend is available."""
        return bool(self.llm_client.get_available_providers())
    
    def get_config_file(self) -> str:
        """Get config file for embedded backend."""
        return "LLM.md"
    
    async def chat(self, message: str, tools: Optional[List[Dict]] = None) -> str:
        """Send message to embedded LLM."""
        messages = [
            {"role": "system", "content": "You are a helpful assistant with access to tools."},
            {"role": "user", "content": message}
        ]
        
        response = await self.llm_client.chat(
            messages=messages,
            tools=tools,
            tool_choice="auto" if tools else None
        )
        
        return response.choices[0].message.content


class BackendManager:
    """Manages different AI backends."""
    
    def __init__(self, llm_client=None):
        self.backends = {
            "claude": ClaudeCodeBackend(),
            "openai": OpenAICodexBackend(),
            "hanzo-dev": HanzoDevBackend(),
            "embedded": EmbeddedBackend(llm_client) if llm_client else None,
        }
        
        self.current_backend = None
        self._auto_select_backend()
        
    def _auto_select_backend(self):
        """Auto-select the best available backend."""
        # Priority order
        priority = ["claude", "openai", "hanzo-dev", "embedded"]
        
        for name in priority:
            backend = self.backends.get(name)
            if backend and backend.is_available():
                self.current_backend = name
                break
    
    def set_backend(self, name: str):
        """Set the current backend."""
        if name not in self.backends:
            raise ValueError(f"Unknown backend: {name}")
        
        backend = self.backends[name]
        if not backend.is_available():
            raise ValueError(f"Backend {name} is not available")
        
        self.current_backend = name
    
    def get_backend(self) -> Backend:
        """Get the current backend."""
        if not self.current_backend:
            raise RuntimeError("No backend available")
        
        return self.backends[self.current_backend]
    
    def list_backends(self) -> Dict[str, bool]:
        """List all backends and their availability."""
        return {
            name: backend.is_available() if backend else False
            for name, backend in self.backends.items()
        }
    
    async def load_config(self) -> Optional[str]:
        """Load configuration from the appropriate file."""
        backend = self.get_backend()
        config_file = backend.get_config_file()
        
        # Look for config file in current directory and parent directories
        paths = [
            Path.cwd() / config_file,
            Path.cwd().parent / config_file,
            Path.home() / f".config/hanzo/{config_file}",
        ]
        
        for path in paths:
            if path.exists():
                return path.read_text()
        
        return None
    
    async def chat(self, message: str, tools: Optional[List[Dict]] = None) -> str:
        """Send chat message using current backend."""
        backend = self.get_backend()
        
        # Load and prepend config if available
        config = await self.load_config()
        if config:
            message = f"Configuration:\n{config}\n\nUser: {message}"
        
        return await backend.chat(message, tools)