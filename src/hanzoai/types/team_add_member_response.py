# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from typing import List, Union, Optional
from datetime import datetime

from pydantic import Field as FieldInfo

from .member import Member
from .._models import BaseModel

__all__ = [
    "TeamAddMemberResponse",
    "UpdatedTeamMembership",
    "UpdatedTeamMembershipLlmBudgetTable",
    "UpdatedUser",
    "UpdatedUserOrganizationMembership",
    "UpdatedUserOrganizationMembershipLlmBudgetTable",
    "LlmModelTable",
]


class UpdatedTeamMembershipLlmBudgetTable(BaseModel):
    budget_duration: Optional[str] = None

    max_budget: Optional[float] = None

    max_parallel_requests: Optional[int] = None

    api_model_max_budget: Optional[object] = FieldInfo(alias="model_max_budget", default=None)

    rpm_limit: Optional[int] = None

    soft_budget: Optional[float] = None

    tpm_limit: Optional[int] = None


class UpdatedTeamMembership(BaseModel):
    budget_id: str

    llm_budget_table: Optional[UpdatedTeamMembershipLlmBudgetTable] = None
    """Represents user-controllable params for a LLM_BudgetTable record"""

    team_id: str

    user_id: str


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


class LlmModelTable(BaseModel):
    created_by: str

    updated_by: str

    api_model_aliases: Union[str, object, None] = FieldInfo(alias="model_aliases", default=None)


class TeamAddMemberResponse(BaseModel):
    team_id: str

    updated_team_memberships: List[UpdatedTeamMembership]

    updated_users: List[UpdatedUser]

    admins: Optional[List[object]] = None

    blocked: Optional[bool] = None

    budget_duration: Optional[str] = None

    budget_reset_at: Optional[datetime] = None

    created_at: Optional[datetime] = None

    llm_model_table: Optional[LlmModelTable] = None

    max_budget: Optional[float] = None

    max_parallel_requests: Optional[int] = None

    members: Optional[List[object]] = None

    members_with_roles: Optional[List[Member]] = None

    metadata: Optional[object] = None

    api_model_id: Optional[int] = FieldInfo(alias="model_id", default=None)

    models: Optional[List[object]] = None

    organization_id: Optional[str] = None

    rpm_limit: Optional[int] = None

    spend: Optional[float] = None

    team_alias: Optional[str] = None

    tpm_limit: Optional[int] = None
