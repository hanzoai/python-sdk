"""llm — models through Hanzo, one tool routed by action (HIP-0300).

    query     POST /v1/chat/completions  one completion; Enso picks the model unless one is named
    models    GET  /v1/models            the catalog with each model's price, searched by text, class, family, capability
    limits    GET  /v1/ai/limits         where the plan stands: shares, states, resets and actions, never a figure
    feedback  POST /v1/ai/feedback       how a routed answer went, so Enso learns from it

The same tool, actions and defaults as the TypeScript (src/tools/llm.ts) and Rust
(rust/src/tools/llm_tool.rs) runtimes of hanzo-mcp. Every call goes to
api.hanzo.ai through the one HanzoCloud client and its credential. A plan refusal
comes back as an error naming its code and the actions (refusal.py).
"""

from typing import Any, ClassVar
from collections.abc import Mapping

from mcp.server.fastmcp import Context as MCPContext

from hanzoai.usage import read_usage
from hanzo_tools.core import BaseTool, ToolError, HanzoCloud, InvalidParamsError
from hanzo_tools.core.cloud import NO_KEY, CloudError

from .refusal import refused

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


#: The classes /v1/models sorts every model into.
CLASSES = ("premium", "ours", "free")
#: What a catalog row can say a model supports beyond text.
SUPPORTS = ("tools", "vision", "reasoning")


def _lower(v: Any) -> str:
    return v.strip().lower() if isinstance(v, str) else ""


def capable(m: dict, c: str) -> bool:
    """Whether a row has a capability: tools, vision or reasoning, or a modality it
    takes or makes (image, audio, embeddings, decision, transcript, ...)."""
    if c in SUPPORTS:
        return m.get(f"supports_{c}") is True

    def has(v: Any) -> bool:
        return isinstance(v, list) and any(str(x).lower() == c for x in v)

    return has(m.get("inputs")) or has(m.get("outputs"))


def catalog(
    body: Any,
    family: str | None = None,
    cls: str | None = None,
    capability: str | None = None,
    search: str | None = None,
) -> dict[str, Any]:
    """One row per model: family, class, what it supports and the price per million
    tokens, as /v1/models states them and never restated here, narrowed by class,
    family, capability and words that must all appear in its id, name, owner or
    description. /v1/models takes no filter, so the narrowing is here."""
    want_cls, want_family, want_cap = _lower(cls), _lower(family), _lower(capability)
    words = _lower(search).split()
    rows = []
    if isinstance(body, dict):
        rows = body.get("data") or body.get("models") or []
    models = []
    for m in rows:
        if not isinstance(m, dict):
            continue
        if want_cls and _lower(m.get("class")) != want_cls:
            continue
        if want_family and _lower(m.get("family")) != want_family:
            continue
        if want_cap and not capable(m, want_cap):
            continue
        if words:
            hay = " ".join(_lower(m.get(k)) for k in ("id", "name", "canonical_slug", "owned_by", "description"))
            if not all(w in hay for w in words):
                continue
        pricing = m.get("pricing") or {}
        models.append(
            {
                "id": m.get("id"),
                "family": m.get("family"),
                "class": m.get("class"),
                "outputs": m.get("outputs"),
                "context_window": m.get("context_window"),
                "supports": [s for s in SUPPORTS if m.get(f"supports_{s}") is True],
                "input_per_million": pricing.get("input_per_million"),
                "output_per_million": pricing.get("output_per_million"),
                # A router SKU is billed at the answering model's cost; its listed
                # price is not what a call costs.
                "variable": pricing.get("variable") is True,
            }
        )
    return {"count": len(models), "models": models}


def _share(w: Any) -> dict[str, Any] | None:
    """The share fields of a usage window: percent, state, resets_at."""
    if not isinstance(w, dict):
        return None
    return {"percent": w.get("percent"), "state": w.get("state"), "resets_at": w.get("resets_at")}


def standing(d: Any) -> dict[str, Any]:
    """Where the plan stands, field by field from /v1/ai/limits: shares (percent),
    states, who pays, resets and actions. Only named fields are copied, so a figure
    the answer might carry never reaches the result."""
    d = d if isinstance(d, dict) else {}
    classes = {
        name: {**(_share(c) or {}), "paying": c.get("paying"), "window": _share(c.get("window"))}
        for name, c in (d.get("classes") or {}).items()
        if isinstance(c, dict)
    }
    lim = d.get("limited")
    return {
        "plan": d.get("plan"),
        "state": d.get("state"),
        "period_start": d.get("period_start"),
        "period_end": d.get("period_end"),
        "classes": classes,
        "session": _share(d.get("session")),
        "day": _share(d.get("day")),
        "limited": {"reason": lim.get("reason"), "classes": lim.get("classes"), "message": lim.get("message")}
        if isinstance(lim, dict)
        else None,
        "paused": [
            {"model": p.get("model"), "fallback": p.get("fallback"), "resets_at": p.get("resets_at")}
            for p in d.get("paused") or []
            if isinstance(p, dict)
        ]
        if isinstance(d.get("paused"), list)
        else None,
        "actions": [
            {k: a.get(k) for k in ("kind", "label", "url", "plan", "model")}
            for a in d.get("actions") or []
            if isinstance(a, dict)
        ],
        "upgrade": d.get("upgrade"),
        "credits_after_allowance": d.get("credits_after_allowance"),
    }


QUERY_SCHEMA = {
    "type": "object",
    "properties": {
        "prompt": {"type": "string", "description": "query: the user message"},
        "system": {"type": "string", "description": "query: an optional system message, with prompt"},
        "messages": {
            "type": "array",
            "items": {"type": "object"},
            "description": "query: the whole conversation as [{role, content}], instead of prompt",
        },
        "model": {
            "type": "string",
            "description": f'query: a model id, "auto", or an enso id (enso-auto, enso-flash, enso-pro, enso-ultra, enso-free); default {DEFAULT_MODEL}',
        },
        "max_tokens": {"type": "integer", "description": "query: the most tokens to generate"},
        "temperature": {"type": "number", "description": "query: sampling temperature"},
        "max_cost": {
            "type": "number",
            "description": "query: the most you will pay, in USD per 1,000 tokens (X-Max-Cost)",
        },
        "max_latency_ms": {
            "type": "number",
            "description": "query: the slowest model you will accept, in milliseconds (X-Max-Latency-Ms)",
        },
        "fallback": {
            "type": "boolean",
            "description": "query: when the plan refuses the model, let its fallback answer instead (X-Hanzo-Fallback: allow)",
        },
    },
    "required": [],
}
MODELS_SCHEMA = {
    "type": "object",
    "properties": {
        "search": {
            "type": "string",
            "description": "models: words that must all appear in the id, name, owner or description",
        },
        "class": {"type": "string", "enum": list(CLASSES), "description": "models: only this class"},
        "family": {"type": "string", "description": "models: only this family, e.g. enso, zen or kai"},
        "capability": {
            "type": "string",
            "description": "models: tools, vision, reasoning, or a modality taken or made (image, audio, embeddings, rerank, transcript, decision)",
        },
    },
    "required": [],
}
LIMITS_SCHEMA = {"type": "object", "properties": {}, "required": []}
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
    VERSION: ClassVar[str] = "0.2.2"
    DEFAULT_ACTION: ClassVar[str] = "query"
    # `class` is a keyword in Python; models takes it as `cls`.
    PARAM_ALIASES: ClassVar[dict[str, str]] = {"class": "cls"}

    def __init__(self):
        super().__init__()
        self._cloud: HanzoCloud | None = None
        self._register_llm_actions()

    @property
    def description(self) -> str:
        return (
            "Models through Hanzo. "
            'query (default): one completion; model defaults to enso-auto, and "auto" lets Enso, '
            "the router, pick across the models your org can serve; max_cost (USD per 1,000 tokens) "
            "and max_latency_ms bound the pick; fallback true lets another model answer when the plan "
            "refuses the one named. Returns {id, model, content, finish_reason, usage, served, paid_by, "
            "usage_state, usage_class, fallback, fallback_reason}: model is the one Enso routed to, "
            "served the SKU that answered, paid_by plan, credits or free, id is what feedback takes. "
            "models: the catalog with each model's family, class (premium, ours, free), what it "
            "supports and price per million input and output tokens; variable true means a router "
            "billed at the answering model's cost. search (words in id, name, owner or description), "
            "class, family and capability (tools, vision, reasoning, or a modality such as image, "
            "audio, embeddings) narrow it. "
            "limits: where your plan stands: its state (ok, near, limited), each class's percent used, "
            "who pays, when it resets, paused models and their fallbacks, and the actions (upgrade, "
            "credits, topup) with their links. "
            "A refusal (402 or 429) is an error naming its code (plan_allowance_used, "
            "paid_plan_required, free_plan_cap, model_cap, usage_cap_exceeded, insufficient_balance) "
            "and its actions. "
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

    async def _send(
        self, method: str, path: str, body: dict | None = None, headers: dict | None = None
    ) -> tuple[Any, Mapping[str, str]]:
        cloud = self._get_cloud()
        try:
            if method == "GET":
                return await cloud.send(method, path)
            return await cloud.send(method, path, headers=headers, json=body or {})
        except CloudError as e:
            raise refused(e)

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
            fallback: bool | None = None,
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
            if fallback is True:
                headers["X-Hanzo-Fallback"] = "allow"
            body: dict[str, Any] = {"model": model or DEFAULT_MODEL, "messages": messages}
            if max_tokens is not None:
                body["max_tokens"] = max_tokens
            if temperature is not None:
                body["temperature"] = temperature
            data, got = await self._send("POST", "/v1/chat/completions", body, headers)
            choice = (data.get("choices") or [{}])[0]
            u = read_usage(got)
            return {
                "id": data.get("id"),
                # The model that served: Enso names it in X-Routed-Model when it
                # rewrote the request, and the body's model always says the same.
                "model": got.get("x-routed-model") or data.get("model"),
                "content": (choice.get("message") or {}).get("content"),
                "finish_reason": choice.get("finish_reason"),
                "usage": data.get("usage"),
                # Who answered and who paid, as the gateway says on the response; a
                # header it did not send is None (a free model sends only served).
                "served": u.served,
                "paid_by": u.paid_by,
                "usage_state": u.usage,
                "usage_class": u.usage_class,
                "fallback": u.fallback,
                "fallback_reason": u.reason,
            }

        @self.action(
            "models", "The catalog with each model's class and per-million price, searched", schema=MODELS_SCHEMA
        )
        async def models(
            ctx: MCPContext,
            search: str | None = None,
            cls: str | None = None,
            family: str | None = None,
            capability: str | None = None,
        ) -> dict:
            if _lower(cls) and _lower(cls) not in CLASSES:
                raise InvalidParamsError(f"class must be one of {', '.join(CLASSES)}", param="class")
            data, _ = await self._send("GET", "/v1/models")
            return catalog(data, family=family, cls=cls, capability=capability, search=search)

        @self.action("limits", "Where your plan stands: shares, states, resets and actions", schema=LIMITS_SCHEMA)
        async def limits(ctx: MCPContext) -> dict:
            data, _ = await self._send("GET", "/v1/ai/limits")
            return standing(data)

        @self.action("feedback", "Tell Enso how a routed answer went", schema=FEEDBACK_SCHEMA)
        async def feedback(
            ctx: MCPContext,
            request_id: str | None = None,
            signal: str | None = None,
            rating: int | None = None,
        ) -> dict:
            if not request_id:
                raise InvalidParamsError(
                    "request_id required: the id of the completion (chatcmpl-...)", param="request_id"
                )
            if signal not in SIGNALS:
                raise InvalidParamsError(f"signal must be one of {', '.join(SIGNALS)}", param="signal")
            body: dict[str, Any] = {"request_id": request_id, "signal": signal}
            if signal == "rating":
                if rating not in (1, 2, 3) or isinstance(rating, bool):
                    raise InvalidParamsError("rating must be 1, 2 or 3 when signal is rating", param="rating")
                body["rating"] = int(rating)
            data, _ = await self._send("POST", "/v1/ai/feedback", body)
            # The /v1 envelope can carry a refusal under a 200.
            if isinstance(data, dict) and data.get("status") == "error":
                raise ToolError(code="UPSTREAM", message=data.get("msg") or "feedback refused")
            return data.get("data", data) if isinstance(data, dict) else data
