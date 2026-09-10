"""The official Python library for the Hanzo API.

Six capabilities hang off one client, and they are the surface almost every
caller wants::

    from hanzoai import Client

    c = Client()  # HANZO_CLIENT_ID / _SECRET
    c.budget.left()  # what is left of the plan
    c.policy.check("usr_7", "write", "graph:acme")
    c.search.find("q3 incident postmortems")
    c.kb.put(Doc(kind="page", title="Runbook", body="…"))
    c.graph.assert_([Fact(entity="acme", relation="tier", value="gold")])
    c.audit.all(Filter(action="graph.assert"))

`budget`, `policy`, `audit`, `search`, `kb` and `graph` are hand-written over
the wire. `hanzoai.cloud` is the generated client for everything else, from
hanzoai/cloud's openapi.yaml at the ref this tree's .spec-lock names, and it is
the only generated client in this distribution.

Names resolve on first use. `hanzoai.cloud` binds 2,479 operations across 2,700
modules and costs real time to import, so nothing here imports it until someone
asks for it — and the six never do.
"""

from typing import TYPE_CHECKING, Any
from importlib import import_module
from importlib.metadata import PackageNotFoundError, version as _version

try:
    # Single-sourced from the installed distribution, never a literal. This said
    # "1.0.0" — the openapi-generator default — while pyproject said 3.1.x, so
    # `hanzoai.__version__` reported a release that never existed.
    __version__ = _version("hanzoai")
except PackageNotFoundError:  # source tree, not installed
    __version__ = "0.0.0+dev"


#: Where each public name lives. One name, one module, so a symbol can never
#: appear in two places and disagree with itself.
_HOME = {
    "cloud": "hanzoai.cloud",
    "Client": "hanzoai.client",
    "Token": "hanzoai.token",
    "Grant": "hanzoai.grant",
    "Reply": "hanzoai.wire",
    "Page": "hanzoai.page",
    "Answer": "hanzoai.answer",
    "Ok": "hanzoai.answer",
    "Denied": "hanzoai.answer",
    "Held": "hanzoai.answer",
    "Fault": "hanzoai.answer",
    "Cure": "hanzoai.answer",
    "Money": "hanzoai.budget",
    "Allowance": "hanzoai.budget",
    "Balance": "hanzoai.budget",
    "Plan": "hanzoai.budget",
    "Charge": "hanzoai.budget",
    "Decision": "hanzoai.policy",
    "Event": "hanzoai.audit",
    "Filter": "hanzoai.audit",
    "Hit": "hanzoai.search",
    "Hits": "hanzoai.search",
    "Match": "hanzoai.search",
    "Backend": "hanzoai.search",
    "Doc": "hanzoai.kb",
    "Connector": "hanzoai.kb",
    "Links": "hanzoai.kb",
    "Fact": "hanzoai.graph",
    "Wrote": "hanzoai.graph",
    "Resolution": "hanzoai.graph",
    "Walk": "hanzoai.graph",
    "Triple": "hanzoai.graph",
    "Vocabulary": "hanzoai.graph",
    "Source": "hanzoai.graph",
}

#: The capability modules, reachable as `hanzoai.budget` and so on.
_MODULES = ("wire", "page", "answer", "token", "grant", "client", "budget", "policy", "audit", "search", "kb", "graph")

__all__ = ["__version__", *_MODULES, *_HOME]


def __getattr__(name: str) -> Any:
    """Resolve a public name to the module that owns it, once."""
    if name in _MODULES or name == "cloud":
        module = import_module("hanzoai." + name)
        globals()[name] = module
        return module
    if name in _HOME:
        value = getattr(import_module(_HOME[name]), name)
        globals()[name] = value
        return value
    if name in ("zap", "ZapTransport", "AsyncZapTransport", "zap_http_client", "async_zap_http_client"):
        # The ZAP-native transport is the `zap` extra: httpx + hanzo-zap, neither
        # a base dependency. Absent, the name is simply not there.
        module = import_module("hanzoai.zap")
        return module if name == "zap" else getattr(module, name)
    raise AttributeError("module 'hanzoai' has no attribute '{0}'".format(name))


def __dir__() -> Any:
    return sorted(__all__)


if TYPE_CHECKING:  # what a type checker and an IDE see, without the import cost
    from hanzoai import cloud as cloud
    from hanzoai.kb import Doc as Doc, Links as Links, Connector as Connector
    from hanzoai.page import Page as Page
    from hanzoai.wire import Reply as Reply
    from hanzoai.audit import Event as Event, Filter as Filter
    from hanzoai.grant import Grant as Grant
    from hanzoai.graph import (
        Fact as Fact,
        Walk as Walk,
        Wrote as Wrote,
        Source as Source,
        Triple as Triple,
        Resolution as Resolution,
        Vocabulary as Vocabulary,
    )
    from hanzoai.token import Token as Token
    from hanzoai.answer import (
        Ok as Ok,
        Cure as Cure,
        Held as Held,
        Fault as Fault,
        Answer as Answer,
        Denied as Denied,
    )
    from hanzoai.budget import (
        Plan as Plan,
        Money as Money,
        Charge as Charge,
        Balance as Balance,
        Allowance as Allowance,
    )
    from hanzoai.client import Client as Client
    from hanzoai.policy import Decision as Decision
    from hanzoai.search import Hit as Hit, Hits as Hits, Match as Match, Backend as Backend
