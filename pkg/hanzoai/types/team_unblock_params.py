# Hanzo AI SDK

from __future__ import annotations

from typing_extensions import Required, TypedDict

__all__ = ["TeamUnblockParams"]


class TeamUnblockParams(TypedDict, total=False):
    team_id: Required[str]
