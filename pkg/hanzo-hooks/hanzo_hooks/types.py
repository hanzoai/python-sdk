"""Types for the hook runner system."""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from enum import Enum


class HookEvent(Enum):
    PreToolUse = "PreToolUse"
    PostToolUse = "PostToolUse"


@dataclass(frozen=True, slots=True)
class HookRunResult:
    denied: bool
    messages: list[str]

    @classmethod
    def allow(cls, messages: list[str] | None = None) -> HookRunResult:
        return cls(denied=False, messages=messages or [])

    def to_permission_outcome(self) -> object:
        """Convert to hanzoai.protocols.PermissionOutcome if available.

        Returns a duck-typed object with .allowed and .reason when the
        hanzoai package is not installed, so callers can use it without
        a hard dependency.
        """
        try:
            from hanzoai.protocols import PermissionOutcome
        except ImportError:
            PermissionOutcome = None

        if PermissionOutcome is not None:
            if self.denied:
                return PermissionOutcome.deny("; ".join(self.messages))
            return PermissionOutcome.allow()

        # Fallback: return a simple namespace matching the protocol.
        if self.denied:
            return _Outcome(allowed=False, reason="; ".join(self.messages))
        return _Outcome(allowed=True, reason="")


@dataclass(frozen=True, slots=True)
class _Outcome:
    """Minimal stand-in for PermissionOutcome when hanzoai is not installed."""
    allowed: bool
    reason: str


@dataclass(frozen=True, slots=True)
class HookConfig:
    """Loadable from settings.json ``hooks`` key."""
    pre_tool_use: list[str] = field(default_factory=list)
    post_tool_use: list[str] = field(default_factory=list)

    @classmethod
    def from_dict(cls, d: dict) -> HookConfig:
        return cls(
            pre_tool_use=list(d.get("pre_tool_use") or d.get("PreToolUse") or []),
            post_tool_use=list(d.get("post_tool_use") or d.get("PostToolUse") or []),
        )

    @classmethod
    def from_json(cls, path: str) -> HookConfig:
        with open(path) as f:
            data = json.load(f)
        hooks = data.get("hooks", data)
        return cls.from_dict(hooks)
