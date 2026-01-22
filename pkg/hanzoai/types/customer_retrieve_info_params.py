# Hanzo AI SDK

from __future__ import annotations

from typing_extensions import Required, TypedDict

__all__ = ["CustomerRetrieveInfoParams"]


class CustomerRetrieveInfoParams(TypedDict, total=False):
    end_user_id: Required[str]
    """End User ID in the request parameters"""
