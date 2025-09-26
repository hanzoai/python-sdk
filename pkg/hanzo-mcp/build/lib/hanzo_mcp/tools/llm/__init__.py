"""LLM tools for Hanzo AI.

This package exposes LLM-related tools. Imports are guarded to keep the
package importable on environments lacking optional dependencies or newer
typing features.
"""

try:  # pragma: no cover - guard heavy imports
    from hanzo_mcp.tools.llm.llm_tool import LLMTool
except Exception:  # pragma: no cover
    LLMTool = None  # type: ignore

try:  # pragma: no cover
    from hanzo_mcp.tools.llm.llm_manage import LLMManageTool
except Exception:
    LLMManageTool = None  # type: ignore

try:  # pragma: no cover
    from hanzo_mcp.tools.llm.consensus_tool import ConsensusTool
except Exception:
    ConsensusTool = None  # type: ignore

try:  # pragma: no cover
    from hanzo_mcp.tools.llm.llm_unified import UnifiedLLMTool
except Exception:
    UnifiedLLMTool = None  # type: ignore

try:  # pragma: no cover
    from hanzo_mcp.tools.llm.provider_tools import (
        GroqTool,
        GeminiTool,
        OpenAITool,
        MistralTool,
        AnthropicTool,
        PerplexityTool,
        create_provider_tools,
    )
except Exception:  # pragma: no cover
    GroqTool = GeminiTool = OpenAITool = MistralTool = AnthropicTool = PerplexityTool = None  # type: ignore

    def create_provider_tools(*args, **kwargs):  # type: ignore
        return []


__all__ = [
    "LLMTool",
    "UnifiedLLMTool",
    "ConsensusTool",
    "LLMManageTool",
    "create_provider_tools",
    "OpenAITool",
    "AnthropicTool",
    "GeminiTool",
    "GroqTool",
    "MistralTool",
    "PerplexityTool",
]
