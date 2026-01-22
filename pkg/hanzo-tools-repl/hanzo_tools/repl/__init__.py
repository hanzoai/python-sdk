"""
hanzo-tools-repl: Multi-language REPL with Jupyter kernel backend.

Provides interactive code evaluation for agents across multiple languages:
- Python (ipykernel)
- Node.js/TypeScript (tslab)
- Bash (bash_kernel)
- And any language with a Jupyter kernel

Usage:
    repl(action="start", language="python")           # Start kernel
    repl(action="eval", code="print('hello')")        # Evaluate code
    repl(action="eval", code="const x = 1", language="typescript")
    repl(action="history")                            # Get history
    repl(action="stop")                               # Stop kernel
    repl(action="list")                               # List kernels
"""

from .repl_tool import ReplTool, KernelManager

TOOLS = [ReplTool()]

__all__ = ["ReplTool", "KernelManager", "TOOLS"]
