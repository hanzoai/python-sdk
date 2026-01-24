# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from __future__ import annotations

from typing import Dict, Union, Optional
from datetime import datetime
from typing_extensions import Annotated, TypedDict

from .._utils import PropertyInfo

__all__ = ["BudgetUpdateParams", "ModelMaxBudget"]


class BudgetUpdateParams(TypedDict, total=False):
    budget_duration: Optional[str]
    """Max duration budget should be set for (e.g. '1hr', '1d', '28d')"""

    budget_id: Optional[str]
    """The unique budget id."""

    budget_reset_at: Annotated[Union[str, datetime, None], PropertyInfo(format="iso8601")]
    """Datetime when the budget is reset"""

    max_budget: Optional[float]
    """Requests will fail if this budget (in USD) is exceeded."""

    max_parallel_requests: Optional[int]
    """Max concurrent requests allowed for this budget id."""

    model_max_budget: Optional[Dict[str, ModelMaxBudget]]
    """Max budget for each model (e.g.

    {'gpt-4o': {'max_budget': '0.0000001', 'budget_duration': '1d', 'tpm_limit':
    1000, 'rpm_limit': 1000}})
    """

    rpm_limit: Optional[int]
    """Max requests per minute, allowed for this budget id."""

    soft_budget: Optional[float]
    """Requests will NOT fail if this is exceeded. Will fire alerting though."""

    tpm_limit: Optional[int]
    """Max tokens per minute, allowed for this budget id."""


class ModelMaxBudget(TypedDict, total=False):
    budget_duration: Optional[str]

    max_budget: Optional[float]

    rpm_limit: Optional[int]

    tpm_limit: Optional[int]
