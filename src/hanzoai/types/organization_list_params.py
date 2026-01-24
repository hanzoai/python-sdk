# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from __future__ import annotations

from typing import Optional
from typing_extensions import TypedDict

__all__ = ["OrganizationListParams"]


class OrganizationListParams(TypedDict, total=False):
    org_alias: Optional[str]
    """Filter organizations by partial organization_alias match.

    Supports case-insensitive search.
    """

    org_id: Optional[str]
    """Filter organizations by exact organization_id match"""
