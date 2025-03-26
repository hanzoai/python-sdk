# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from typing import Optional
from typing_extensions import Literal

from pydantic import Field as FieldInfo

from .._models import BaseModel

__all__ = ["CustomerRetrieveInfoResponse", "LlmBudgetTable"]


class LlmBudgetTable(BaseModel):
    budget_duration: Optional[str] = None

    max_budget: Optional[float] = None

    max_parallel_requests: Optional[int] = None

    api_model_max_budget: Optional[object] = FieldInfo(alias="model_max_budget", default=None)

    rpm_limit: Optional[int] = None

    soft_budget: Optional[float] = None

    tpm_limit: Optional[int] = None


class CustomerRetrieveInfoResponse(BaseModel):
    blocked: bool

    user_id: str

    alias: Optional[str] = None

    allowed_model_region: Optional[Literal["eu", "us"]] = None

    default_model: Optional[str] = None

    llm_budget_table: Optional[LlmBudgetTable] = None
    """Represents user-controllable params for a LLM_BudgetTable record"""

    spend: Optional[float] = None
