"""Hanzo Agents - Multi-agent orchestration for Hanzo AI.

This package provides a CLI and library for running and orchestrating
multiple AI agents including Claude, Codex, Gemini, Grok, and more.

Usage:
    # CLI
    hanzo-agents run claude "Explain this code"
    hanzo-agents list
    hanzo-agents status

    # Library
    from hanzo_agents import run_agent, list_agents
    result = await run_agent("claude", "Explain this code")
"""

__version__ = "0.1.2"

from hanzo_tools.agent import AgentTool, IChingTool, ReviewTool

__all__ = [
    "__version__",
    "AgentTool",
    "IChingTool",
    "ReviewTool",
]
