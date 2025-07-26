# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from __future__ import annotations

from typing import Optional
from typing_extensions import TypedDict

__all__ = ["UserListParams"]


class UserListParams(TypedDict, total=False):
    page: int
    """Page number"""

    page_size: int
    """Number of items per page"""

    role: Optional[str]
    """Filter users by role"""

    user_ids: Optional[str]
    """Get list of users by user_ids"""
