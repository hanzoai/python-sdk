# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from __future__ import annotations

from typing import Optional
from typing_extensions import TypedDict

__all__ = ["SpendListTagsParams"]


class SpendListTagsParams(TypedDict, total=False):
    end_date: Optional[str]
    """Time till which to view key spend"""

    start_date: Optional[str]
    """Time from which to start viewing key spend"""

    tags: Optional[str]
    """comman separated tags to filter on"""
