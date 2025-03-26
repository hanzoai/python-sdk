# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from typing import List, Optional
from datetime import datetime

from pydantic import Field as FieldInfo

from .._models import BaseModel

__all__ = [
    "OrganizationAddMemberResponse",
    "UpdatedOrganizationMembership",
    "UpdatedOrganizationMembershipLlmBudgetTable",
    "UpdatedUser",
    "UpdatedUserOrganizationMembership",
    "UpdatedUserOrganizationMembershipLlmBudgetTable",
]


class UpdatedOrganizationMembershipLlmBudgetTable(BaseModel):
    budget_duration: Optional[str] = None

    max_budget: Optional[float] = None

    max_parallel_requests: Optional[int] = None

    api_model_max_budget: Optional[object] = FieldInfo(alias="model_max_budget", default=None)

    rpm_limit: Optional[int] = None

    soft_budget: Optional[float] = None

    tpm_limit: Optional[int] = None


class UpdatedOrganizationMembership(BaseModel):
    created_at: datetime

    organization_id: str

    updated_at: datetime

    user_id: str

    budget_id: Optional[str] = None

    llm_budget_table: Optional[UpdatedOrganizationMembershipLlmBudgetTable] = None
    """Represents user-controllable params for a LLM_BudgetTable record"""

    spend: Optional[float] = None

    user: Optional[object] = None

    user_role: Optional[str] = None


class UpdatedUserOrganizationMembershipLlmBudgetTable(BaseModel):
    budget_duration: Optional[str] = None

    max_budget: Optional[float] = None

    max_parallel_requests: Optional[int] = None

    api_model_max_budget: Optional[object] = FieldInfo(alias="model_max_budget", default=None)

    rpm_limit: Optional[int] = None

    soft_budget: Optional[float] = None

    tpm_limit: Optional[int] = None


class UpdatedUserOrganizationMembership(BaseModel):
    created_at: datetime

    organization_id: str

    updated_at: datetime

    user_id: str

    budget_id: Optional[str] = None

    llm_budget_table: Optional[UpdatedUserOrganizationMembershipLlmBudgetTable] = None
    """Represents user-controllable params for a LLM_BudgetTable record"""

    spend: Optional[float] = None

    user: Optional[object] = None

    user_role: Optional[str] = None


class UpdatedUser(BaseModel):
    user_id: str

    budget_duration: Optional[str] = None

    budget_reset_at: Optional[datetime] = None

    max_budget: Optional[float] = None

    metadata: Optional[object] = None

    api_model_max_budget: Optional[object] = FieldInfo(alias="model_max_budget", default=None)

    api_model_spend: Optional[object] = FieldInfo(alias="model_spend", default=None)

    models: Optional[List[object]] = None

    organization_memberships: Optional[List[UpdatedUserOrganizationMembership]] = None

    rpm_limit: Optional[int] = None

    spend: Optional[float] = None

    sso_user_id: Optional[str] = None

    teams: Optional[List[str]] = None

    tpm_limit: Optional[int] = None

    user_email: Optional[str] = None

    user_role: Optional[str] = None


class OrganizationAddMemberResponse(BaseModel):
    organization_id: str

    updated_organization_memberships: List[UpdatedOrganizationMembership]

    updated_users: List[UpdatedUser]
