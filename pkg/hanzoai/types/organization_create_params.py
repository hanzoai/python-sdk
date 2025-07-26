# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from __future__ import annotations

from typing import Iterable, Optional
from typing_extensions import Required, TypedDict

__all__ = ["OrganizationCreateParams"]


class OrganizationCreateParams(TypedDict, total=False):
    organization_alias: Required[str]

    budget_duration: Optional[str]

    budget_id: Optional[str]

    max_budget: Optional[float]

    max_parallel_requests: Optional[int]

    metadata: Optional[object]

    model_max_budget: Optional[object]

    models: Iterable[object]

    organization_id: Optional[str]

    rpm_limit: Optional[int]

    soft_budget: Optional[float]

    tpm_limit: Optional[int]
