"""kai_decide — Kai, Hanzo's decision model, at POST /v1/decisions.

One state, any named typed questions, one call: the same tool, name and contract
as the TypeScript (src/tools/kai.ts) and Rust (rust/src/tools/kai_tool.rs)
runtimes. A question is {type, instructions, criteria}: ``choice`` picks a label,
``score`` an ordinal level, ``noul`` the probability a statement holds. Answers
come back with calibrated probabilities, and Kai writes no text.
"""

from typing import Any, ClassVar

from mcp.server.fastmcp import Context as MCPContext

from hanzo_tools.core import BaseTool, HanzoCloud, InvalidParamsError, ToolError
from hanzo_tools.core.cloud import NO_KEY, CloudError

#: The model a decision is asked of when none is named.
DEFAULT_MODEL = "kai"
KINDS = ("choice", "score", "noul")


def _content(v: Any) -> bool:
    """Text, an object or an array: the wire's Content."""
    return isinstance(v, (str, dict, list))


def fault(q: Any) -> str:
    """What is wrong with one question under the wire contract, or ''."""
    if not isinstance(q, dict):
        return "must be {type, instructions, criteria}"
    kind = q.get("type")
    if kind not in KINDS:
        return f"type must be one of {', '.join(KINDS)}"
    if q.get("instructions") is not None and not _content(q["instructions"]):
        return "instructions must be text, an object or an array"
    c = q.get("criteria")
    if kind == "choice":
        if isinstance(c, list):
            if not all(isinstance(label, str) for label in c):
                return "criteria as a list must hold string labels"
            n = len(set(c))
        elif isinstance(c, dict):
            n = len(c)
        else:
            return "criteria must be {label: description} or [label, ...]"
        return "" if n >= 2 else f"criteria must name at least 2 labels, not {n}"
    if kind == "score":
        if not isinstance(c, list):
            return "criteria must be the levels, lowest first: [level0, level1, ...]"
        if not c:
            return "criteria must list at least 1 level"
        nulls = [i for i, level in enumerate(c) if level is None]
        return f"score level {nulls[0]} is null; describe every level" if nulls else ""
    if c is None:
        return ""
    if not isinstance(c, dict):
        return 'criteria must be {"true": ..., "false": ...}'
    odd = [k for k in c if str(k).lower() not in ("true", "false")]
    return f'criteria take only "true" and "false", not {", ".join(odd)}' if odd else ""


def request(state: Any, questions: Any, model: Any = None) -> dict[str, Any]:
    """Check a decision's shape and build its body; whether a state fits the model
    is the server's to say (422 state_too_long)."""
    if not _content(state):
        raise InvalidParamsError("state required: text, an object or an array", param="state")
    if not isinstance(questions, dict):
        raise InvalidParamsError("questions required: {name: {type, instructions, criteria}}", param="questions")
    if not 1 <= len(questions) <= 100:
        raise InvalidParamsError(f"questions must hold 1 to 100 questions, not {len(questions)}", param="questions")
    for name, q in questions.items():
        f = fault(q)
        if f:
            raise InvalidParamsError(f"question '{name}': {f}", param="questions")
    m = model or DEFAULT_MODEL
    if not isinstance(m, str):
        raise InvalidParamsError("model must be a model name, e.g. kai", param="model")
    return {"model": m, "state": state, "questions": questions}


DECIDE_SCHEMA = {
    "type": "object",
    "properties": {
        "state": {"type": ["string", "object", "array"], "items": {}, "description": "The case to decide about: text, a JSON object or an array"},
        "questions": {
            "type": "object",
            "description": "Question name → {type, instructions, criteria}; 1 to 100 questions",
            "additionalProperties": {
                "type": "object",
                "properties": {
                    "type": {"type": "string", "enum": list(KINDS)},
                    "instructions": {"type": ["string", "object", "array"], "items": {}, "description": "Optional, recommended. What Kai answers"},
                    "criteria": {
                        "type": ["object", "array"],
                        "items": {},
                        "description": 'choice: {label: description} or [label, ...], 2 labels or more; score: [level0, level1, ...], lowest first, none null; noul: {"true": ..., "false": ...}, optional',
                    },
                },
                "required": ["type"],
            },
        },
        "model": {"type": "string", "description": "Decision model (default kai)"},
    },
    "required": ["state", "questions"],
}


class KaiDecideTool(BaseTool):
    """Typed questions to Kai about one case, answered with calibrated probabilities."""

    name: ClassVar[str] = "kai_decide"
    VERSION: ClassVar[str] = "0.2.1"
    DEFAULT_ACTION: ClassVar[str] = "decide"

    def __init__(self):
        super().__init__()
        self._cloud: HanzoCloud | None = None

        @self.action("decide", "Ask Kai typed questions about one case", schema=DECIDE_SCHEMA)
        async def decide(ctx: MCPContext, state: Any = None, questions: Any = None, model: str | None = None) -> dict:
            body = request(state, questions, model)
            if self._cloud is None:
                self._cloud = HanzoCloud()
            if not self._cloud.configured():
                raise ToolError(code="INVALID_PARAMS", message=NO_KEY)
            try:
                d = await self._cloud.post("/v1/decisions", body)
            except CloudError as e:
                raise ToolError(code="UPSTREAM", message=str(e))
            if not isinstance(d, dict) or not isinstance(d.get("answers"), dict):
                raise ToolError(code="UPSTREAM", message=f"not a decision: {str(d)[:200]}")
            return d

    @property
    def description(self) -> str:
        return (
            "Ask Kai, Hanzo's decision model, typed questions about one case in one call (POST /v1/decisions). "
            "Reach for Kai when the answer is one of options you already know: classify, route, gate, rank, check. "
            "It writes no text. `questions` maps a name to {type, instructions, criteria}, 1 to 100 of them; "
            "`instructions` is optional but recommended, as the text Kai answers. choice picks one label: criteria "
            "{label: description} or [label, ...], 2 labels or more. score picks an ordinal level: criteria "
            "[level0, level1, ...], lowest first; act on the argmax of its probabilities, since score is the mean "
            'level index. noul gives the probability a statement holds: criteria {"true": ..., "false": ...}, '
            "optional; write it as a statement, not a bare yes/no question. Returns the decision {id, model, "
            "answers: {name: answer}, usage, routing, state_hash, latency_ms}. Probabilities are calibrated; "
            "confidence = (n·p_max − 1)/(n − 1) over n options. Billed on input tokens at the catalog's kai rate; "
            "output_tokens is 0."
        )
