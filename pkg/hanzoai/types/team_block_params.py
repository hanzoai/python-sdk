# Hanzo AI SDK

from __future__ import annotations

from typing_extensions import Required, TypedDict

__all__ = ["TeamBlockParams"]


class TeamBlockParams(TypedDict, total=False):
    team_id: Required[str]
