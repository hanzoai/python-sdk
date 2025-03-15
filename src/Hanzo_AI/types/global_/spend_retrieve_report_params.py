# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from __future__ import annotations

from typing import Optional
from typing_extensions import Literal, TypedDict

__all__ = ["SpendRetrieveReportParams"]


class SpendRetrieveReportParams(TypedDict, total=False):
    api_key: Optional[str]
    """View spend for a specific api_key. Example api_key='sk-1234"""

    customer_id: Optional[str]
    """View spend for a specific customer_id.

    Example customer_id='1234. Can be used in conjunction with team_id as well.
    """

    end_date: Optional[str]
    """Time till which to view spend"""

    group_by: Optional[Literal["team", "customer", "api_key"]]
    """Group spend by internal team or customer or api_key"""

    internal_user_id: Optional[str]
    """View spend for a specific internal_user_id. Example internal_user_id='1234"""

    start_date: Optional[str]
    """Time from which to start viewing spend"""

    team_id: Optional[str]
    """View spend for a specific team_id. Example team_id='1234"""
