# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from __future__ import annotations

from typing import Optional
from typing_extensions import TypedDict

from .._types import SequenceNotStr

__all__ = ["OrganizationUpdateParams"]


class OrganizationUpdateParams(TypedDict, total=False):
    budget_id: Optional[str]

    metadata: Optional[object]

    models: Optional[SequenceNotStr[str]]

    organization_alias: Optional[str]

    organization_id: Optional[str]

    spend: Optional[float]

    updated_by: Optional[str]
