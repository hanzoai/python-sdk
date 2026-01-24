# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from __future__ import annotations

from typing import Optional
from typing_extensions import TypedDict

from .._types import SequenceNotStr

__all__ = ["KeyListParams"]


class KeyListParams(TypedDict, total=False):
    expand: Optional[SequenceNotStr[str]]
    """Expand related objects (e.g. 'user')"""

    include_created_by_keys: bool
    """Include keys created by the user"""

    include_team_keys: bool
    """Include all keys for teams that user is an admin of."""

    key_alias: Optional[str]
    """Filter keys by key alias"""

    key_hash: Optional[str]
    """Filter keys by key hash"""

    organization_id: Optional[str]
    """Filter keys by organization ID"""

    page: int
    """Page number"""

    return_full_object: bool
    """Return full key object"""

    size: int
    """Page size"""

    sort_by: Optional[str]
    """Column to sort by (e.g. 'user_id', 'created_at', 'spend')"""

    sort_order: str
    """Sort order ('asc' or 'desc')"""

    status: Optional[str]
    """Filter by status (e.g. 'deleted')"""

    team_id: Optional[str]
    """Filter keys by team ID"""

    user_id: Optional[str]
    """Filter keys by user ID"""
