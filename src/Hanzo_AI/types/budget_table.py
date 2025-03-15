# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from typing import Optional

from pydantic import Field as FieldInfo

from .._models import BaseModel

__all__ = ["BudgetTable"]


class BudgetTable(BaseModel):
    budget_duration: Optional[str] = None

    max_budget: Optional[float] = None

    max_parallel_requests: Optional[int] = None

    api_model_max_budget: Optional[object] = FieldInfo(alias="model_max_budget", default=None)

    rpm_limit: Optional[int] = None

    soft_budget: Optional[float] = None

    tpm_limit: Optional[int] = None
