# Copyright 2026 Hanzo AI, Inc. All rights reserved.
"""Value types for the Hanzo flags client — the same shapes @hanzo/flags carries.

A flag value is ``True`` (a boolean flag that is on), a non-empty ``str`` (the
active variant of a multivariate flag), or absent (off). The result also carries
per-flag JSON payloads and a soft error signal, matching the PostHog ``/decide``
response the cloud ``/v1/flags`` endpoint returns.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, Optional

# A flag evaluates to a bool (on/off) or a variant name.
FlagValue = Any  # bool | str


@dataclass(frozen=True)
class Group:
    """One group the caller belongs to (org, team, …) for group-targeted flags."""

    key: str
    properties: Optional[Dict[str, Any]] = None


@dataclass(frozen=True)
class EvalContext:
    """Who is being evaluated. ``distinct_id`` is required; the rest refine targeting.

    Mirrors @hanzo/flags EvalContext: distinctId / personProperties / groups.
    """

    distinct_id: str
    person_properties: Optional[Dict[str, Any]] = None
    groups: Optional[Dict[str, Group]] = None

    def wire(self) -> Dict[str, Any]:
        """The request body the /v1/flags endpoint expects (PostHog-shaped)."""
        body: Dict[str, Any] = {"distinct_id": self.distinct_id}
        if self.person_properties:
            body["person_properties"] = self.person_properties
        if self.groups:
            body["groups"] = {
                k: {"key": g.key, **({"properties": g.properties} if g.properties else {})}
                for k, g in self.groups.items()
            }
        return body


@dataclass
class EvalResult:
    """A resolved set of flags — the same three fields @hanzo/flags returns.

    ``errors_while_computing`` is a SOFT signal: the client is fail-open, so a
    transport error yields the last good (or empty) result with this set True,
    never an exception on the hot path.
    """

    feature_flags: Dict[str, FlagValue] = field(default_factory=dict)
    feature_flag_payloads: Dict[str, Any] = field(default_factory=dict)
    errors_while_computing: bool = False

    @classmethod
    def from_wire(cls, body: Dict[str, Any]) -> "EvalResult":
        return cls(
            feature_flags=body.get("featureFlags") or {},
            feature_flag_payloads=body.get("featureFlagPayloads") or {},
            errors_while_computing=bool(body.get("errorsWhileComputingFlags")),
        )

    def is_enabled(self, key: str) -> bool:
        """True when the flag is on: boolean ``True`` OR any non-empty variant."""
        v = self.feature_flags.get(key)
        return v is True or (isinstance(v, str) and v != "")

    def variant(self, key: str) -> Optional[str]:
        """The active variant of a multivariate flag, or ``None``."""
        v = self.feature_flags.get(key)
        return v if isinstance(v, str) else None

    def payload(self, key: str) -> Any:
        """The flag's JSON payload (per-variant or the ``true`` payload), or ``None``."""
        return self.feature_flag_payloads.get(key)
