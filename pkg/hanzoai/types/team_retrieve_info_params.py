# Hanzo AI SDK

from __future__ import annotations

from typing_extensions import TypedDict

__all__ = ["TeamRetrieveInfoParams"]


class TeamRetrieveInfoParams(TypedDict, total=False):
    team_id: str
    """Team ID in the request parameters"""
