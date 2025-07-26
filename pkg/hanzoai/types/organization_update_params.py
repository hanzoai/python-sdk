# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from __future__ import annotations

from typing import List, Optional
from typing_extensions import TypedDict

__all__ = ["OrganizationUpdateParams"]


class OrganizationUpdateParams(TypedDict, total=False):
    budget_id: Optional[str]

    metadata: Optional[object]

    models: Optional[List[str]]

    organization_alias: Optional[str]

    organization_id: Optional[str]

    spend: Optional[float]

    updated_by: Optional[str]
