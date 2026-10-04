"""llm — models through Hanzo, one tool routed by action (HIP-0300).

    query     POST /v1/chat/completions  one completion; Enso picks the model unless one is named
    models    GET  /v1/models            the catalog with each model's price, as the gateway states it
    feedback  POST /v1/ai/feedback       how a routed answer went, so Enso learns from it

The same tool, actions and defaults as the TypeScript (src/tools/llm.ts) and Rust
(rust/src/tools/llm_tool.rs) runtimes of hanzo-mcp. Every call goes to
api.hanzo.ai through the one HanzoCloud client and its credential.
"""

from typing import Any, ClassVar

from mcp.server.fastmcp import Context as MCPContext

from hanzo_tools.core import BaseTool, HanzoCloud, InvalidParamsError, ToolError
from hanzo_tools.core.cloud import NO_KEY, CloudError

#: Enso's managed default: the id Hanzo Dev sends when no model is named.
DEFAULT_MODEL = "enso-auto"

#: The signals /v1/ai/feedback takes.
SIGNALS = ("up", "accept", "regenerate", "down", "switch", "abandon", "revert", "rating", "dismiss")


def bounds(max_cost: float | None, max_latency_ms: float | None) -> dict[str, str]:
    """Enso's two routing bounds as the headers it reads; an unset one is not sent."""
    out: dict[str, str] = {}
    for name, header, value in (
        ("max_cost", "X-Max-Cost", max_cost),
        ("max_latency_ms", "X-Max-Latency-Ms", max_latency_ms),
    ):
        if value is None or value == "":
            continue
        try:
            n = float(value)
        except (TypeError, ValueError):
            n = float("nan")
        if not n > 0 or n == float("inf"):
            raise InvalidParamsError(f"{name} must be a positive number, not {value!r}", param=name)
        out[header] = str(round(n)) if name == "max_latency_ms" else format(n, "g")
    return out


def catalog(body: Any, family: str | None = None) -> dict[str, Any]:
    """One row per model: family, class, outputs, context window and the price per
    million tokens, as /v1/models states them and never restated here."""
    rows = []
    if isinstance(body, dict):
        rows = body.get("data") or body.get("models") or []
    want = (family or "").lower()
    models = []
    for m in rows:
        if want and str(m.get("family") or "").lower() != want:
            continue
        pricing = m.get("pricing") or {}
        models.append(
            {
                "id": m.get("id"),
                "family": m.get("family"),
                "class": m.get("class"),
                "outputs": m.get("outputs"),
                "context_window": m.get("context_window"),
                "input_per_million": pricing.get("input_per_million"),
                "output_per_million": pricing.get("output_per_million"),
            }
        )
    return {"count": len(models), "models": models}


QUERY_SCHEMA = {
    "type": "object",
    "properties": {
        "prompt": {"type": "string", "description": "query: the user message"},
        "system": {"type": "string", "description": "query: an optional system message, with prompt"},
        "messages": {"type": "array", "items": {"type": "object"}, "description": "query: the whole conversation as [{role, content}], instead of prompt"},
        "model": {"type": "string", "description": f'query: a model id, "auto", or an enso id (enso-auto, enso-flash, enso-pro, enso-ultra, enso-free); default {DEFAULT_MODEL}'},
        "max_tokens": {"type": "integer", "description": "query: the most tokens to generate"},
        "temperature": {"type": "number", "description": "query: sampling temperature"},
        "max_cost": {"type": "number", "description": "query: the most you will pay, in USD per 1,000 tokens (X-Max-Cost)"},
        "max_latency_ms": {"type": "number", "description": "query: the slowest model you will accept, in milliseconds (X-Max-Latency-Ms)"},
    },
    "required": [],
}
MODELS_SCHEMA = {
    "type": "object",
    "properties": {"family": {"type": "string", "description": "models: only this family, e.g. enso or kai"}},
    "required": [],
}
FEEDBACK_SCHEMA = {
    "type": "object",
    "properties": {
        "request_id": {"type": "string", "description": "feedback: the completion id query returned (chatcmpl-...)"},
        "signal": {"type": "string", "enum": list(SIGNALS), "description": "feedback: how the answer went"},
        "rating": {"type": "integer", "enum": [1, 2, 3], "description": "feedback: 1 to 3, with signal rating"},
    },
    "required": [],
}


class UnifiedLLMTool(BaseTool):
    """Models through api.hanzo.ai: completions routed by Enso, the catalog, feedback."""

    name: ClassVar[str] = "llm"
    VERSION: ClassVar[str] = "0.2.1"
    DEFAULT_ACTION: ClassVar[str] = "query"

    def __init__(self):
        super().__init__()
        self._cloud: HanzoCloud | None = None
        self._register_llm_actions()

    @property
    def description(self) -> str:
        return (
            "Models through Hanzo. "
            "query (default): one completion; model defaults to enso-auto, and \"auto\" lets Enso, "
            "the router, pick across the models your org can serve; max_cost (USD per 1,000 tokens) "
            "and max_latency_ms bound the pick; returns {id, model, content, finish_reason, usage}, "
            "where model is the one that served and id is what feedback takes. "
            "models: the catalog with each model's family, class and price per million input and "
            "output tokens (family filters, e.g. enso or kai). "
            "feedback: tell Enso how a routed answer went: request_id is the completion id, signal one of "
            + ", ".join(SIGNALS)
            + ", and rating 1 to 3 with signal rating. Typed decisions are kai_decide's, not a completion's."
        )

    def _get_cloud(self) -> HanzoCloud:
        if self._cloud is None:
            self._cloud = HanzoCloud()
        if not self._cloud.configured():
            raise ToolError(code="INVALID_PARAMS", message=NO_KEY)
        return self._cloud

    async def _send(self, method: str, path: str, body: dict | None = None, headers: dict | None = None) -> Any:
        cloud = self._get_cloud()
        try:
            if method == "GET":
                return await cloud.get(path)
            return await cloud.post(path, body, headers=headers)
        except CloudError as e:
            raise ToolError(code="UPSTREAM", message=str(e))

    def _register_llm_actions(self):
        @self.action("query", "One completion; Enso routes it unless a model is named", schema=QUERY_SCHEMA)
        async def query(
            ctx: MCPContext,
            prompt: str | None = None,
            system: str | None = None,
            messages: list | None = None,
            model: str = DEFAULT_MODEL,
            max_tokens: int | None = None,
            temperature: float | None = None,
            max_cost: float | None = None,
            max_latency_ms: float | None = None,
        ) -> dict:
            if messages is None:
                if not prompt:
                    raise InvalidParamsError("prompt or messages required", param="prompt")
                messages = ([{"role": "system", "content": system}] if system else []) + [
                    {"role": "user", "content": prompt}
                ]
            elif not isinstance(messages, list) or not messages:
                raise InvalidParamsError("messages must be a non-empty array of {role, content}", param="messages")
            headers = bounds(max_cost, max_latency_ms)
            body: dict[str, Any] = {"model": model or DEFAULT_MODEL, "messages": messages}
            if max_tokens is not None:
                body["max_tokens"] = max_tokens
            if temperature is not None:
                body["temperature"] = temperature
            data = await self._send("POST", "/v1/chat/completions", body, headers)
            choice = (data.get("choices") or [{}])[0]
            return {
                "id": data.get("id"),
                # The model that served. Enso also names it in X-Routed-Model; the
                # body's model always says the same.
                "model": data.get("model"),
                "content": (choice.get("message") or {}).get("content"),
                "finish_reason": choice.get("finish_reason"),
                "usage": data.get("usage"),
            }

        @self.action("models", "The catalog with each model's family, class and per-million price", schema=MODELS_SCHEMA)
        async def models(ctx: MCPContext, family: str | None = None) -> dict:
            return catalog(await self._send("GET", "/v1/models"), family)

        @self.action("feedback", "Tell Enso how a routed answer went", schema=FEEDBACK_SCHEMA)
        async def feedback(
            ctx: MCPContext,
            request_id: str | None = None,
            signal: str | None = None,
            rating: int | None = None,
        ) -> dict:
            if not request_id:
                raise InvalidParamsError("request_id required: the id of the completion (chatcmpl-...)", param="request_id")
            if signal not in SIGNALS:
                raise InvalidParamsError(f"signal must be one of {', '.join(SIGNALS)}", param="signal")
            body: dict[str, Any] = {"request_id": request_id, "signal": signal}
            if signal == "rating":
                if rating not in (1, 2, 3) or isinstance(rating, bool):
                    raise InvalidParamsError("rating must be 1, 2 or 3 when signal is rating", param="rating")
                body["rating"] = int(rating)
            data = await self._send("POST", "/v1/ai/feedback", body)
            # The /v1 envelope can carry a refusal under a 200.
            if isinstance(data, dict) and data.get("status") == "error":
                raise ToolError(code="UPSTREAM", message=data.get("msg") or "feedback refused")
            return data.get("data", data) if isinstance(data, dict) else data
