"""Consensus tool using Metastable protocol."""

import asyncio
from typing import List, Optional, Annotated, final, override

from pydantic import Field
from hanzo_consensus import Result as ConsensusResult, run as run_consensus
from mcp.server.fastmcp import Context as MCPContext

from hanzo_tools.core import BaseTool, auto_timeout, create_tool_context

from .llm_unified import LLMTool


@final
class ConsensusTool(BaseTool):
    """Metastable consensus across multiple LLMs.

    https://github.com/luxfi/consensus
    """

    name = "consensus"

    DEFAULT_MODELS = [
        "gpt-4o-mini",
        "claude-3-5-sonnet-20241022",
        "gemini/gemini-1.5-pro",
    ]

    def __init__(self):
        self.llm_tool = LLMTool()

    @property
    @override
    def description(self) -> str:
        return """Metastable consensus across multiple LLMs.

Two-phase protocol:
- Phase I (Sampling): Models propose, k-peer sampling, confidence
- Phase II (Finality): Threshold aggregation, winner synthesis

Usage:
  consensus --prompt "Best approach?" --models '["gpt-4", "claude-3-5-sonnet"]'
  consensus --prompt "Review this" --rounds 2 --k 2

Reference: https://github.com/luxfi/consensus
"""

    @override
    @auto_timeout("consensus")
    async def call(
        self,
        ctx: MCPContext,
        prompt: Annotated[str, Field(description="Query")] = "",
        models: Annotated[Optional[List[str]], Field(description="Models")] = None,
        rounds: Annotated[int, Field(description="Sampling rounds")] = 3,
        k: Annotated[int, Field(description="Sample size")] = 3,
        alpha: Annotated[float, Field(description="Agreement")] = 0.6,
        beta_1: Annotated[float, Field(description="Preference")] = 0.5,
        beta_2: Annotated[float, Field(description="Decision")] = 0.8,
        temperature: Annotated[float, Field(description="Temperature")] = 0.7,
        **kwargs,
    ) -> str:
        """Run Metastable consensus."""
        tool_ctx = create_tool_context(ctx)
        await tool_ctx.set_tool_info(self.name)

        if not prompt:
            return "Error: prompt required"

        model_list = models or self.DEFAULT_MODELS

        # Filter to available models
        available = []
        for m in model_list:
            provider = self.llm_tool._get_provider_for_model(m)
            if provider in self.llm_tool.available_providers:
                available.append(m)

        if not available:
            return "Error: No models available"

        await tool_ctx.info(f"Metastable consensus: {len(available)} models, {rounds} rounds")

        # Execute adapter
        async def execute(model: str, model_prompt: str) -> ConsensusResult:
            try:
                import time

                start = time.time()
                result = await self.llm_tool.call(
                    ctx,
                    model=model,
                    prompt=model_prompt,
                    temperature=temperature,
                )
                ms = int((time.time() - start) * 1000)
                return ConsensusResult(id=model, output=result, ok=True, ms=ms)
            except Exception as e:
                return ConsensusResult(id=model, output="", ok=False, error=str(e))

        # Run consensus
        state = await run_consensus(
            prompt=prompt,
            participants=available,
            execute=execute,
            rounds=rounds,
            k=min(k, len(available)),
            alpha=alpha,
            beta_1=beta_1,
            beta_2=beta_2,
        )

        lines = [
            "=== Metastable Consensus ===",
            f"Models: {', '.join(available)}",
            f"Rounds: {rounds}, k={k}",
            f"Winner: {state.winner}",
            f"Finalized: {state.finalized}",
            "",
            "=== Synthesis ===",
            state.synthesis or "(no synthesis)",
        ]

        return "\n".join(lines)

    def register(self, mcp_server) -> None:
        """Register with MCP server."""
        pass
