"""Tool configuration registry.

Discovers tools from hanzo-tools-* entry points and provides a unified
registry for enable/disable, CLI flag generation, and mode filtering.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from enum import Enum
from importlib.metadata import entry_points
from typing import Optional

from hanzo_mcp.tools.common.entrypoint_loader import (
    TOOLS_ENTRY_POINT_GROUP,
    tool_identity,
)

logger = logging.getLogger(__name__)


class ToolCategory(Enum):
    filesystem = "filesystem"
    shell = "shell"
    code = "code"
    search = "search"
    vcs = "vcs"
    reasoning = "reasoning"
    memory = "memory"
    todo = "todo"
    config = "config"
    agent = "agent"
    browser = "browser"
    computer = "computer"
    lsp = "lsp"
    refactor = "refactor"
    net = "net"
    llm = "llm"
    api = "api"
    auth = "auth"
    ui = "ui"
    other = "other"


@dataclass
class ToolConfigEntry:
    """Metadata for a single tool."""

    name: str
    description: str = ""
    category: ToolCategory = ToolCategory.other
    enabled: bool = True
    package: Optional[str] = None
    cli_flag: str = ""
    dependencies: list[str] = field(default_factory=list)


# Category guessing from tool name prefix
_PREFIX_TO_CATEGORY: dict[str, ToolCategory] = {
    "fs": ToolCategory.filesystem,
    "read": ToolCategory.filesystem,
    "write": ToolCategory.filesystem,
    "edit": ToolCategory.filesystem,
    "tree": ToolCategory.filesystem,
    "exec": ToolCategory.shell,
    "run": ToolCategory.shell,
    "zsh": ToolCategory.shell,
    "code": ToolCategory.code,
    "grep": ToolCategory.search,
    "find": ToolCategory.search,
    "search": ToolCategory.search,
    "git": ToolCategory.vcs,
    "think": ToolCategory.reasoning,
    "critic": ToolCategory.reasoning,
    "memory": ToolCategory.memory,
    "tasks": ToolCategory.todo,
    "todo": ToolCategory.todo,
    "config": ToolCategory.config,
    "mode": ToolCategory.config,
    "agent": ToolCategory.agent,
    "zen": ToolCategory.agent,
    "review": ToolCategory.agent,
    "browser": ToolCategory.browser,
    "computer": ToolCategory.computer,
    "lsp": ToolCategory.lsp,
    "refactor": ToolCategory.refactor,
    "fetch": ToolCategory.net,
    "curl": ToolCategory.net,
    "wget": ToolCategory.net,
    "llm": ToolCategory.llm,
    "consensus": ToolCategory.llm,
    "api": ToolCategory.api,
    "hanzo": ToolCategory.api,
    "auth": ToolCategory.auth,
    "ui": ToolCategory.ui,
}


def _guess_category(name: str) -> ToolCategory:
    for prefix, cat in _PREFIX_TO_CATEGORY.items():
        if name == prefix or name.startswith(prefix + "_"):
            return cat
    return ToolCategory.other


class DynamicToolRegistry:
    """Discovers tools from entry points and exposes them as ToolConfigEntry."""

    _entries: dict[str, ToolConfigEntry] = {}
    _initialized: bool = False

    @classmethod
    def initialize(cls) -> None:
        if cls._initialized:
            return
        cls._initialized = True
        cls._entries = {}
        try:
            eps = entry_points(group=TOOLS_ENTRY_POINT_GROUP)
            for ep in eps:
                try:
                    tools_list = ep.load()
                    if not isinstance(tools_list, list):
                        continue
                    for tool_class in tools_list:
                        name, desc = tool_identity(tool_class)
                        cls._entries[name] = ToolConfigEntry(
                            name=name,
                            description=desc,
                            category=_guess_category(name),
                            enabled=True,
                            package=ep.name,
                            cli_flag=f"--{name.replace('_', '-')}",
                        )
                except Exception as e:
                    logger.debug(f"Failed to load entry point '{ep.name}': {e}")
        except Exception as e:
            logger.debug(f"Failed to discover entry points: {e}")

    @classmethod
    def get(cls, name: str) -> Optional[ToolConfigEntry]:
        cls.initialize()
        return cls._entries.get(name)

    @classmethod
    def list_all(cls) -> dict[str, ToolConfigEntry]:
        cls.initialize()
        return dict(cls._entries)

    @classmethod
    def reset(cls) -> None:
        """Reset for testing."""
        cls._entries = {}
        cls._initialized = False


# Module-level convenience -- DynamicToolRegistry doubles as the dict-like TOOL_REGISTRY.
# Code that does `TOOL_REGISTRY.items()` or `TOOL_REGISTRY.keys()` works via __getattr__.
class _RegistryProxy:
    """Thin proxy so ``TOOL_REGISTRY.items()`` and ``TOOL_REGISTRY.keys()`` work."""

    def keys(self):
        DynamicToolRegistry.initialize()
        return DynamicToolRegistry._entries.keys()

    def values(self):
        DynamicToolRegistry.initialize()
        return DynamicToolRegistry._entries.values()

    def items(self):
        DynamicToolRegistry.initialize()
        return DynamicToolRegistry._entries.items()

    def __len__(self):
        DynamicToolRegistry.initialize()
        return len(DynamicToolRegistry._entries)

    def __iter__(self):
        DynamicToolRegistry.initialize()
        return iter(DynamicToolRegistry._entries)

    def __getitem__(self, key: str):
        DynamicToolRegistry.initialize()
        return DynamicToolRegistry._entries[key]

    def get(self, key: str, default=None):
        DynamicToolRegistry.initialize()
        return DynamicToolRegistry._entries.get(key, default)


TOOL_REGISTRY = _RegistryProxy()
