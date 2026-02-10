# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from __future__ import annotations

from typing import Optional
from typing_extensions import TypedDict

__all__ = ["KeyListParams"]


class KeyListParams(TypedDict, total=False):
    include_team_keys: bool
    """Include all keys for teams that user is an admin of."""

    key_alias: Optional[str]
    """Filter keys by key alias"""

    organization_id: Optional[str]
    """Filter keys by organization ID"""

    page: int
    """Page number"""

    return_full_object: bool
    """Return full key object"""

    size: int
    """Page size"""

    team_id: Optional[str]
    """Filter keys by team ID"""

    user_id: Optional[str]
    """Filter keys by user ID"""
