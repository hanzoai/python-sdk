"""May this subject take this action on this object.

Policy appears twice and the two speak one vocabulary. Before a call,
:meth:`Policy.check` answers `allow` as a plain boolean — asking whether you may
is a question with an answer, not a refusal. During a call, a request a policy
stops comes back as :class:`hanzoai.Denied` with code ``policy_denied``, or as
:class:`hanzoai.Held` naming the clause a person still has to clear. The clause
in a hold names the same clause a check would have refused on.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any
from dataclasses import dataclass

from hanzoai.wire import flag, text

if TYPE_CHECKING:
    from hanzoai.client import Client

__all__ = ["Decision", "Policy"]


@dataclass(frozen=True)
class Decision:
    """The verdict, with the question beside it.

    A cached or logged decision that does not carry its own question is a
    boolean nobody can audit. `reason` is empty until cloud fills it.
    """

    allow: bool = False
    sub: str = ""
    act: str = ""
    obj: str = ""
    reason: str = ""

    @classmethod
    def read(cls, body: Any, sub: str, act: str, obj: str) -> "Decision":
        return cls(
            allow=flag(body, "allow"),
            sub=text(body, "sub") or sub,
            act=text(body, "act") or act,
            obj=text(body, "obj") or obj,
            reason=text(body, "reason"),
        )


class Policy:
    """`c.policy`."""

    def __init__(self, client: "Client") -> None:
        self.client = client

    def check(self, sub: str, act: str, obj: str) -> Decision:
        """Ask whether `sub` may `act` on `obj`. All three are required.

        The arguments read in the order the sentence does — subject, verb,
        object. Cloud's body orders its members ``{sub, obj, act}``; the request
        is built that way here, once, so no caller has to hold both orders.

        Hand-written rather than generated: the route declares neither a request
        body nor a response, so every generator emits a method that takes
        nothing and returns nothing.
        """
        body = self.client.read("POST", "/v1/authz/check", body={"sub": sub, "obj": obj, "act": act})
        return Decision.read(body, sub, act, obj)
