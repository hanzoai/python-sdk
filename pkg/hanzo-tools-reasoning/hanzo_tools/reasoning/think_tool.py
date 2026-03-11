"""Unified thinking tool implementation (HIP-0300).

This module provides the ThinkTool with action-based dispatch for
all reasoning operations: think, critic, review, consensus, summarize,
classify, explain, translate, compare, chain, agent, embed.
"""

from typing import ClassVar

from mcp.server.fastmcp import Context as MCPContext

from hanzo_tools.core import BaseTool


class ThinkTool(BaseTool):
    """Unified thinking and reasoning tool (HIP-0300).

    Actions:
    - think: Structured thinking and brainstorming (default)
    - critic: Critical analysis and devil's advocate
    - review: Code review and quality analysis
    - consensus: Multi-perspective consensus reasoning
    - agent: Agent-style step-by-step reasoning
    - summarize: Summarize content concisely
    - classify: Classify content into categories
    - explain: Explain a concept clearly
    - translate: Translate between formats/languages
    - compare: Compare multiple items
    - chain: Chain-of-thought multi-step reasoning
    - embed: Generate embedding representation (placeholder)
    """

    name: ClassVar[str] = "think"
    VERSION: ClassVar[str] = "0.3.0"

    def __init__(self) -> None:
        super().__init__()
        self._register_think_actions()

    @property
    def description(self) -> str:
        return """Unified reasoning tool (HIP-0300).

Actions:
- think: Structured thinking and brainstorming (default)
- critic: Critical analysis, devil's advocate
- review: Code review and quality check
- consensus: Multi-perspective reasoning
- agent: Step-by-step agent reasoning
- summarize: Summarize content
- classify: Classify into categories
- explain: Explain a concept
- translate: Translate between formats
- compare: Compare items
- chain: Chain-of-thought reasoning
- embed: Embedding representation (placeholder)
"""

    def _register_think_actions(self):
        """Register all thinking actions."""

        @self.action("think", "Structured thinking and brainstorming")
        async def think(ctx: MCPContext, thought: str = "", **kwargs) -> str:
            """Record a structured thought process.

            Args:
                thought: The thought to record
            """
            if not thought or not thought.strip():
                return "Error: 'thought' parameter is required"
            return "Thinking recorded. Continue with your next action based on this analysis."

        @self.action("critic", "Critical analysis and devil's advocate")
        async def critic(ctx: MCPContext, analysis: str = "", thought: str = "", **kwargs) -> str:
            """Perform critical analysis.

            Args:
                analysis: The critical analysis to perform
                thought: Alternative param name for the analysis
            """
            text = analysis or thought
            if not text or not text.strip():
                return "Error: 'analysis' or 'thought' parameter is required"
            return """Critical analysis complete. Remember to:
1. Address all identified issues before proceeding
2. Run comprehensive tests to verify fixes
3. Ensure all tests pass with proper coverage
4. Document any design decisions or trade-offs
5. Consider the analysis points in your implementation"""

        @self.action("review", "Code review and quality analysis")
        async def review(ctx: MCPContext, code: str = "", thought: str = "", **kwargs) -> str:
            """Perform code review.

            Args:
                code: Code or description to review
                thought: Alternative param name
            """
            text = code or thought
            if not text or not text.strip():
                return "Error: 'code' or 'thought' parameter is required"
            return "Code review recorded. Apply findings to improve quality, correctness, and maintainability."

        @self.action("consensus", "Multi-perspective consensus reasoning")
        async def consensus(ctx: MCPContext, topic: str = "", perspectives: int = 3, thought: str = "", **kwargs) -> str:
            """Reason from multiple perspectives to reach consensus.

            Args:
                topic: The topic to reason about
                perspectives: Number of perspectives to consider
                thought: Alternative param name
            """
            text = topic or thought
            if not text or not text.strip():
                return "Error: 'topic' or 'thought' parameter is required"
            return f"Consensus reasoning recorded ({perspectives} perspectives). Use the synthesized viewpoint to guide decisions."

        @self.action("agent", "Agent-style step-by-step reasoning")
        async def agent(ctx: MCPContext, goal: str = "", thought: str = "", **kwargs) -> str:
            """Perform agent-style reasoning with goal decomposition.

            Args:
                goal: The goal to reason about
                thought: Alternative param name
            """
            text = goal or thought
            if not text or not text.strip():
                return "Error: 'goal' or 'thought' parameter is required"
            return "Agent reasoning recorded. Execute the planned steps sequentially."

        @self.action("summarize", "Summarize content concisely")
        async def summarize(ctx: MCPContext, content: str = "", thought: str = "", max_length: int = 0, **kwargs) -> str:
            """Summarize content.

            Args:
                content: Content to summarize
                thought: Alternative param name
                max_length: Optional max length hint
            """
            text = content or thought
            if not text or not text.strip():
                return "Error: 'content' or 'thought' parameter is required"
            return "Summary recorded. Use the condensed version for communication or documentation."

        @self.action("classify", "Classify content into categories")
        async def classify(ctx: MCPContext, content: str = "", categories: str = "", thought: str = "", **kwargs) -> str:
            """Classify content into categories.

            Args:
                content: Content to classify
                categories: Comma-separated category options
                thought: Alternative param name
            """
            text = content or thought
            if not text or not text.strip():
                return "Error: 'content' or 'thought' parameter is required"
            return "Classification recorded. Apply the categorization to guide next steps."

        @self.action("explain", "Explain a concept clearly")
        async def explain(ctx: MCPContext, concept: str = "", audience: str = "developer", thought: str = "", **kwargs) -> str:
            """Explain a concept.

            Args:
                concept: Concept to explain
                audience: Target audience (developer, beginner, expert)
                thought: Alternative param name
            """
            text = concept or thought
            if not text or not text.strip():
                return "Error: 'concept' or 'thought' parameter is required"
            return f"Explanation recorded (audience: {audience}). Use for documentation or communication."

        @self.action("translate", "Translate between formats or languages")
        async def translate(ctx: MCPContext, content: str = "", target: str = "", thought: str = "", **kwargs) -> str:
            """Translate content between formats or languages.

            Args:
                content: Content to translate
                target: Target format or language
                thought: Alternative param name
            """
            text = content or thought
            if not text or not text.strip():
                return "Error: 'content' or 'thought' parameter is required"
            target_desc = f" to {target}" if target else ""
            return f"Translation{target_desc} recorded. Apply the translated version."

        @self.action("compare", "Compare multiple items")
        async def compare(ctx: MCPContext, items: str = "", criteria: str = "", thought: str = "", **kwargs) -> str:
            """Compare items against criteria.

            Args:
                items: Items to compare (comma-separated or description)
                criteria: Comparison criteria
                thought: Alternative param name
            """
            text = items or thought
            if not text or not text.strip():
                return "Error: 'items' or 'thought' parameter is required"
            return "Comparison recorded. Use the analysis to make an informed decision."

        @self.action("chain", "Chain-of-thought multi-step reasoning")
        async def chain(ctx: MCPContext, steps: str = "", thought: str = "", **kwargs) -> str:
            """Perform chain-of-thought reasoning.

            Args:
                steps: The reasoning steps
                thought: Alternative param name
            """
            text = steps or thought
            if not text or not text.strip():
                return "Error: 'steps' or 'thought' parameter is required"
            return "Chain-of-thought reasoning recorded. Follow the logical progression to reach the conclusion."

        @self.action("embed", "Generate embedding representation (placeholder)")
        async def embed(ctx: MCPContext, content: str = "", thought: str = "", **kwargs) -> str:
            """Placeholder for embedding generation.

            Args:
                content: Content to embed
                thought: Alternative param name
            """
            text = content or thought
            if not text or not text.strip():
                return "Error: 'content' or 'thought' parameter is required"
            return "Embedding placeholder recorded. Use a dedicated embedding service for production vectors."
