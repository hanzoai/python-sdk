"""Models through Hanzo, as MCP tools.

Tools:
- llm: completions routed by Enso, the model catalog with prices, feedback
- kai_decide: typed questions to Kai, Hanzo's decision model

Every call reaches api.hanzo.ai through hanzo_tools.core.HanzoCloud.
"""

from .kai import KaiDecideTool
from .llm_unified import UnifiedLLMTool

TOOLS = [UnifiedLLMTool, KaiDecideTool]

__all__ = ["TOOLS", "UnifiedLLMTool", "KaiDecideTool"]
