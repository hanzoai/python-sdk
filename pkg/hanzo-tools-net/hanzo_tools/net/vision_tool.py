"""Vision tool for HIP-0300 architecture.

Sends an image to a Hanzo vision model (api.hanzo.ai /v1/chat/completions,
OpenAI-compatible) and returns the model's answer. The default SKU is
``zen3-vl`` (``GET /v1/models`` also lists ``zen3-omni``); override via ``model``.

Effect lattice position: NONDETERMINISTIC_EFFECT (cloud inference).
"""

import base64
import mimetypes
import os
from pathlib import Path
from typing import Any, ClassVar

from mcp.server.fastmcp import Context as MCPContext

from hanzo_tools.core import (
    BaseTool,
    HanzoCloud,
    InvalidParamsError,
    NotFoundError,
    ToolError,
)

DEFAULT_VISION_MODEL = "zen3-vl"


class VisionTool(BaseTool):
    """Vision-language tool: image (+ prompt) → text answer (HIP-0300)."""

    name: ClassVar[str] = "vision"
    VERSION: ClassVar[str] = "0.1.0"

    def __init__(self, cwd: str | None = None):
        super().__init__()
        self.cwd = cwd or os.getcwd()
        self._cloud: HanzoCloud | None = None
        self._register_vision_actions()

    @property
    def description(self) -> str:
        return """Vision-language tool (HIP-0300).

Actions:
- ask: Ask a question about an image (image + prompt → text)
- describe: Describe an image (image → text)

Image accepts a local file path, an http(s) URL, or a data: URI.
Backed by api.hanzo.ai /v1/chat/completions (default model: zen3-vl).

Effect: NONDETERMINISTIC_EFFECT (cloud inference)
"""

    def _get_cloud(self) -> HanzoCloud:
        if self._cloud is None:
            self._cloud = HanzoCloud()
        if not self._cloud.configured():
            raise ToolError(
                code="INVALID_PARAMS",
                message="Hanzo Cloud not configured: set HANZO_API_KEY "
                "or add .apiKey to ~/.hanzo/config.json",
            )
        return self._cloud

    async def _image_url(self, image: str) -> str:
        """Normalize an image reference to an inline data: URI.

        A data: URI passes through; a local path is read and encoded; an http(s)
        URL is fetched and encoded (the vision backend takes inline images, not
        remote URLs). Encoding here makes every input path work uniformly.
        """
        if image.startswith("data:"):
            return image
        if image.startswith(("http://", "https://")):
            try:
                import httpx

                async with httpx.AsyncClient(
                    follow_redirects=True,
                    timeout=30.0,
                    headers={"User-Agent": "Mozilla/5.0 (compatible; HanzoBot/1.0)"},
                ) as client:
                    resp = await client.get(image)
                    resp.raise_for_status()
            except Exception as e:
                raise ToolError(
                    code="INTERNAL_ERROR",
                    message=f"could not fetch image: {e}",
                    details={"image": image},
                )
            mime = resp.headers.get("content-type", "image/png").split(";")[0].strip()
            b64 = base64.b64encode(resp.content).decode("ascii")
            return f"data:{mime};base64,{b64}"
        p = Path(image) if Path(image).is_absolute() else Path(self.cwd) / image
        if not p.exists():
            raise NotFoundError(f"Image not found: {image}", uri=str(p))
        mime = mimetypes.guess_type(p.name)[0] or "image/png"
        b64 = base64.b64encode(p.read_bytes()).decode("ascii")
        return f"data:{mime};base64,{b64}"

    async def _complete(
        self, image: str, prompt: str, model: str, max_tokens: int
    ) -> dict:
        content = [
            {"type": "text", "text": prompt},
            {"type": "image_url", "image_url": {"url": await self._image_url(image)}},
        ]
        body: dict[str, Any] = {
            "model": model,
            "messages": [{"role": "user", "content": content}],
            "max_tokens": max_tokens,
        }
        data = await self._get_cloud().post("/v1/chat/completions", body)
        choices = data.get("choices") or []
        answer = ""
        if choices:
            answer = (choices[0].get("message") or {}).get("content") or ""
        return {
            "answer": answer,
            "model": data.get("model", model),
            "usage": data.get("usage"),
        }

    def _register_vision_actions(self):
        @self.action("ask", "Ask a question about an image")
        async def ask(
            ctx: MCPContext,
            image: str,
            prompt: str = "Describe this image in detail.",
            model: str = DEFAULT_VISION_MODEL,
            max_tokens: int = 1024,
        ) -> dict:
            """Ask a vision model about an image.

            Args:
                image: Local path, http(s) URL, or data: URI
                prompt: Question / instruction
                model: Vision SKU (default zen3-vl)
                max_tokens: Max response tokens

            Returns:
                {answer, model, usage}
            """
            if not image:
                raise InvalidParamsError("image is required", param="image")
            return await self._complete(image, prompt, model, max_tokens)

        @self.action("describe", "Describe an image")
        async def describe(
            ctx: MCPContext,
            image: str,
            model: str = DEFAULT_VISION_MODEL,
            max_tokens: int = 1024,
        ) -> dict:
            """Describe an image (convenience wrapper over ask)."""
            if not image:
                raise InvalidParamsError("image is required", param="image")
            return await self._complete(
                image, "Describe this image in detail.", model, max_tokens
            )


# Singleton
vision_tool = VisionTool
