"""Regression: a tool whose `description` is a @property must not crash `tool list`.

Bug: DynamicToolRegistry stored `getattr(tool_class, "description")`, which for a
class-level @property returns the property DESCRIPTOR (not a str). Later
`len(config.description)` in `tool list` raised:
    object of type 'property' has no len()
This made the whole `tool list` action unusable.
"""

from hanzo_mcp.config.tool_config import (
    DynamicToolRegistry,
    _extract_tool_description,
)


class _PropDescTool:
    """A tool that exposes `description` only via an instance @property."""

    name = "propdesc"

    @property
    def description(self) -> str:  # noqa: D401
        return "described via property"


class _PropDescNoInstanceTool:
    """A @property that blows up without proper init — must degrade to ''."""

    name = "propdesc_bad"

    def __init__(self):
        raise RuntimeError("cannot instantiate cheaply")

    @property
    def description(self) -> str:
        return "unreachable"


class _PlainDescTool:
    name = "plaindesc"
    description = "a plain string description"


class _NoDescTool:
    name = "nodesc"


def test_extract_property_description_is_a_string():
    # The @property is resolved to its real string value (via a cheap instance).
    assert _extract_tool_description(_PropDescTool) == "described via property"
    # Every branch returns a real str — never a `property` object.
    for cls in (_PropDescTool, _PropDescNoInstanceTool, _PlainDescTool, _NoDescTool):
        assert isinstance(_extract_tool_description(cls), str)
    # A property that can't be evaluated degrades to empty, not a crash.
    assert _extract_tool_description(_PropDescNoInstanceTool) == ""
    assert _extract_tool_description(_PlainDescTool) == "a plain string description"
    assert _extract_tool_description(_NoDescTool) == ""


def test_registered_entry_descriptions_are_never_property_objects():
    # The bug's fingerprint: len() on a stored description must always work,
    # i.e. every registered entry's description is a real str.
    DynamicToolRegistry.reset()
    DynamicToolRegistry.initialize()
    for name, entry in DynamicToolRegistry.list_all().items():
        assert isinstance(entry.description, str), (
            f"{name} description is {type(entry.description).__name__}, not str"
        )
        # This is the exact op that used to crash.
        _ = len(entry.description)
