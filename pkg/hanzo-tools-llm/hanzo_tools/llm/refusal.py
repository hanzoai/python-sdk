"""A failed cloud call as a tool error; a plan refusal names its code and the ways on.

api.hanzo.ai refuses what the plan, a cap or the balance will not pay for with a
402 or 429 whose ``error.code`` names why. ``hanzoai.usage.refusal`` reads it, the
same reader the SDK raises its typed errors from, and the error leads with that
code, as the TypeScript and Rust runtimes' do (src/tools/refusal.ts). It carries
what the server offers: the class, the capped model and its fallback, the spent
window, when it resets, and the actions (upgrade, switch, credits, topup). The
message is the server's own sentence, which names no figure; nothing else in the
body is passed on, so no amount, count or cap reaches a tool result from here.
"""

from typing import Any

from hanzoai.wire import Reply, stamp
from hanzoai.usage import refusal
from hanzo_tools.core import ToolError
from hanzo_tools.core.cloud import CloudError


def refused(e: CloudError) -> ToolError:
    """The ToolError for a failed call: the refusal's own code when it is one, else UPSTREAM."""
    r = refusal(Reply(status=e.status or 0, body=e.body))
    if r is None:
        return ToolError(code="UPSTREAM", message=str(e))
    actions: list[dict[str, Any]] = [{k: v for k, v in vars(a).items() if v} for a in r.actions if a.kind]
    if r.upgrade_url and not any(a.get("url") == r.upgrade_url for a in actions):
        actions.insert(0, {"kind": "upgrade", "url": r.upgrade_url})
    details = {
        "status": r.status,
        "class": r.usage_class,
        "model": r.model,
        "fallback": r.fallback,
        "window": r.window,
        "resets_at": stamp(r.resets_at) or None,
        "actions": actions,
    }
    return ToolError(code=r.code, message=r.message, details={k: v for k, v in details.items() if v is not None})
