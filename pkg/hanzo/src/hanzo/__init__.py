"""Hanzo — one import, and the rest of the stack behind it.

`hanzo` is a front door, the same one the npm package and the Rust crate are.
It composes; it does not reimplement. Each piece keeps living in its own
distribution, and this names them:

    import hanzo
    hanzo.cloud     # the Open AI Cloud client, generated from the document
    hanzo.mcp       # tools over the Model Context Protocol
    hanzo.agents    # the agent runtime
    hanzo.cli       # the command line

Nothing above is imported until it is touched. That matters here more than it
does in JavaScript, where a subpath is resolved per import and an unused one
costs nothing: a Python package body runs on `import`, so naming these eagerly
would have made `import hanzo` pay for click, rich, httpx and every optional
dependency in the list, whether or not the caller wanted the CLI. `__getattr__`
(PEP 562) defers each to first use and caches it in the module namespace, so
the second touch is a dict lookup.

It also unties a knot: `hanzo.cli` reads `__version__` back off this module, so
importing it from the module body was a cycle that only worked because the
version happened to be assigned above it.
"""

from importlib import import_module
from importlib.metadata import PackageNotFoundError, version as _version

try:
    # The installed distribution is the single source of the version. Hardcoding
    # it here meant three declarations (pyproject 0.4.4, this file 0.3.47,
    # cli.py 0.3.48) that drifted apart, so `hanzo --version` reported a release
    # that did not exist and no one could tell what they were actually running.
    __version__ = _version("hanzo")
except PackageNotFoundError:  # running from a source tree, not installed
    __version__ = "0.0.0+dev"

# name here -> the distribution's import name. One table: adding a member of the
# stack is one line, and there is no second place that has to agree with it.
_ELSEWHERE = {
    "cloud": "hanzoai",
    "mcp": "hanzo_mcp",
    "agents": "hanzo_agents",
    "memory": "hanzo_memory",
    "network": "hanzo_network",
    "tools": "hanzo_tools",
    "kms": "hanzo_kms",
    "iam": "hanzo_iam",
}

# Submodules of this package, deferred for the same reason.
_OWN = ("cli",)

__all__ = ["__version__", "cli", "main", *sorted(_ELSEWHERE)]


def __getattr__(name: str):
    """Import a member of the stack the first time it is named."""
    if name in _OWN:
        mod = import_module(f".{name}", __name__)
    elif name in _ELSEWHERE:
        try:
            mod = import_module(_ELSEWHERE[name])
        except ModuleNotFoundError as exc:
            dist = _ELSEWHERE[name].replace("_", "-")
            raise AttributeError(
                f"hanzo.{name} needs the {dist} distribution, which is not installed: "
                f"pip install {dist}"
            ) from exc
    elif name == "main":
        mod = import_module(".cli", __name__)
        return mod.main
    else:
        raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
    globals()[name] = mod
    return mod


def __dir__() -> list[str]:
    return sorted(set(__all__) | set(globals()))
