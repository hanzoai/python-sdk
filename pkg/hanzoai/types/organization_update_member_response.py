# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from typing import Optional
from datetime import datetime

from pydantic import Field as FieldInfo

from .._models import BaseModel

__all__ = ["OrganizationUpdateMemberResponse", "LlmBudgetTable"]


class LlmBudgetTable(BaseModel):
    budget_duration: Optional[str] = None

    max_budget: Optional[float] = None

    max_parallel_requests: Optional[int] = None

    api_model_max_budget: Optional[object] = FieldInfo(alias="model_max_budget", default=None)

    rpm_limit: Optional[int] = None

    soft_budget: Optional[float] = None

    tpm_limit: Optional[int] = None


class OrganizationUpdateMemberResponse(BaseModel):
    created_at: datetime

    organization_id: str

    updated_at: datetime

    user_id: str

    budget_id: Optional[str] = None

    llm_budget_table: Optional[LlmBudgetTable] = None
    """Represents user-controllable params for a LLM_BudgetTable record"""

    spend: Optional[float] = None

    user: Optional[object] = None

    user_role: Optional[str] = None
