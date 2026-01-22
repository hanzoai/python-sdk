# Hanzo AI SDK

from __future__ import annotations

from typing import Optional
from typing_extensions import TypedDict

__all__ = ["UserRetrieveInfoParams"]


class UserRetrieveInfoParams(TypedDict, total=False):
    user_id: Optional[str]
    """User ID in the request parameters"""
