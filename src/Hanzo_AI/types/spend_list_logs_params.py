# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from __future__ import annotations

from typing import Optional
from typing_extensions import TypedDict

__all__ = ["SpendListLogsParams"]


class SpendListLogsParams(TypedDict, total=False):
    api_key: Optional[str]
    """Get spend logs based on api key"""

    end_date: Optional[str]
    """Time till which to view key spend"""

    request_id: Optional[str]
    """request_id to get spend logs for specific request_id.

    If none passed then pass spend logs for all requests
    """

    start_date: Optional[str]
    """Time from which to start viewing key spend"""

    user_id: Optional[str]
    """Get spend logs based on user_id"""
