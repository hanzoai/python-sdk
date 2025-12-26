"""Hanzo Tools - Modular tool packages for AI agents.

This is the namespace package for all hanzo-tools-* packages.
Each tool category is a separate installable package:

  pip install hanzo-tools-core        # Base infrastructure
  pip install hanzo-tools-filesystem  # File operations
  pip install hanzo-tools-shell       # Shell/command execution
  pip install hanzo-tools-browser     # Browser automation
  pip install hanzo-tools-agent       # Agent orchestration
  pip install hanzo-tools-llm         # LLM integrations
  pip install hanzo-tools-database    # Database tools
  pip install hanzo-tools-memory      # Memory/knowledge base
  pip install hanzo-tools-editor      # Editor integrations
  pip install hanzo-tools-jupyter     # Jupyter notebook tools
  pip install hanzo-tools-lsp         # Language server protocol
  pip install hanzo-tools-refactor    # Code refactoring
  pip install hanzo-tools-vector      # Vector search
  pip install hanzo-tools-todo        # Task management

Or install all at once:
  pip install hanzo-tools[all]
"""

__path__ = __import__("pkgutil").extend_path(__path__, __name__)
