"""
Bridge to Rust MCP implementation with Python fallback

Provides seamless integration with Rust-based tools when available,
falling back to pure Python implementations for compatibility.
"""

import json
import subprocess
import shutil
from pathlib import Path
from typing import Any, Dict, List, Optional
from abc import ABC, abstractmethod
import logging

logger = logging.getLogger(__name__)


class McpBridge(ABC):
    """Abstract base class for MCP tool execution"""
    
    @abstractmethod
    async def list_tools(self) -> List[Dict[str, Any]]:
        """List all available tools"""
        pass
    
    @abstractmethod
    async def execute(self, tool_name: str, params: Dict[str, Any]) -> Any:
        """Execute a tool by name"""
        pass


class RustBridge(McpBridge):
    """Bridge to Rust-based MCP tools for performance"""
    
    def __init__(self):
        self.rust_binary = self._find_rust_binary()
        if not self.rust_binary:
            raise RuntimeError("Rust MCP binary not found")
    
    def _find_rust_binary(self) -> Optional[Path]:
        """Find the dev-mcp Rust binary"""
        possible_paths = [
            # Development paths
            Path(__file__).parent.parent.parent.parent.parent / "dev/src/rs/target/release/dev",
            Path(__file__).parent.parent.parent.parent.parent / "dev/src/rs/target/debug/dev",
            # Installed paths
            Path("/usr/local/bin/dev"),
            Path.home() / ".cargo/bin/dev",
        ]
        
        # Check if 'dev' is in PATH
        if shutil.which("dev"):
            return Path(shutil.which("dev"))
        
        for path in possible_paths:
            if path.exists() and path.is_file():
                logger.info(f"Found Rust MCP binary at: {path}")
                return path
        
        return None
    
    def _run_rust_command(self, args: List[str]) -> str:
        """Run a Rust MCP command and return output"""
        try:
            result = subprocess.run(
                [str(self.rust_binary), "mcp"] + args,
                capture_output=True,
                text=True,
                check=True,
                timeout=30
            )
            return result.stdout
        except subprocess.CalledProcessError as e:
            logger.error(f"Rust command failed: {e.stderr}")
            raise RuntimeError(f"Rust MCP error: {e.stderr}")
        except subprocess.TimeoutExpired:
            raise RuntimeError("Rust MCP command timed out")
    
    async def list_tools(self) -> List[Dict[str, Any]]:
        """List tools from Rust implementation"""
        output = self._run_rust_command(["list-tools", "--format", "json"])
        return json.loads(output)
    
    async def execute(self, tool_name: str, params: Dict[str, Any]) -> Any:
        """Execute a tool via Rust implementation"""
        output = self._run_rust_command([
            "call",
            tool_name,
            "--params",
            json.dumps(params)
        ])
        return json.loads(output)


class PythonBridge(McpBridge):
    """Pure Python implementation of MCP tools"""
    
    def __init__(self):
        from .tools import ToolRegistry
        self.registry = ToolRegistry()
        self._register_all_tools()
    
    def _register_all_tools(self):
        """Register all Python tool implementations"""
        # Import and register tools from each category
        from .tools import file, search, shell, edit, git, ast, browser, ai, project
        
        file.register_tools(self.registry)
        search.register_tools(self.registry)
        shell.register_tools(self.registry)
        edit.register_tools(self.registry)
        git.register_tools(self.registry)
        ast.register_tools(self.registry)
        browser.register_tools(self.registry)
        ai.register_tools(self.registry)
        project.register_tools(self.registry)
    
    async def list_tools(self) -> List[Dict[str, Any]]:
        """List all Python tools"""
        return self.registry.list_tools()
    
    async def execute(self, tool_name: str, params: Dict[str, Any]) -> Any:
        """Execute a Python tool"""
        return await self.registry.execute(tool_name, params)


def create_bridge() -> McpBridge:
    """
    Create the appropriate MCP bridge.
    
    Tries to use Rust implementation first for performance,
    falls back to Python if Rust is unavailable.
    """
    try:
        bridge = RustBridge()
        logger.info("Using Rust MCP implementation")
        return bridge
    except RuntimeError:
        logger.info("Rust MCP not available, using Python implementation")
        return PythonBridge()