# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from typing import List, Union, Optional
from datetime import datetime

from pydantic import Field as FieldInfo

from . import member
from .._models import BaseModel

__all__ = [
    "OrganizationUpdateResponse",
    "LlmBudgetTable",
    "Member",
    "MemberLlmBudgetTable",
    "Team",
    "TeamLlmModelTable",
]


class LlmBudgetTable(BaseModel):
    budget_duration: Optional[str] = None

    max_budget: Optional[float] = None

    max_parallel_requests: Optional[int] = None

    api_model_max_budget: Optional[object] = FieldInfo(alias="model_max_budget", default=None)

    rpm_limit: Optional[int] = None

    soft_budget: Optional[float] = None

    tpm_limit: Optional[int] = None


class MemberLlmBudgetTable(BaseModel):
    budget_duration: Optional[str] = None

    max_budget: Optional[float] = None

    max_parallel_requests: Optional[int] = None

    api_model_max_budget: Optional[object] = FieldInfo(alias="model_max_budget", default=None)

    rpm_limit: Optional[int] = None

    soft_budget: Optional[float] = None

    tpm_limit: Optional[int] = None


class Member(BaseModel):
    created_at: datetime

    organization_id: str

    updated_at: datetime

    user_id: str

    budget_id: Optional[str] = None

    llm_budget_table: Optional[MemberLlmBudgetTable] = None
    """Represents user-controllable params for a LLM_BudgetTable record"""

    spend: Optional[float] = None

    user: Optional[object] = None

    user_role: Optional[str] = None


class TeamLlmModelTable(BaseModel):
    created_by: str

    updated_by: str

    api_model_aliases: Union[str, object, None] = FieldInfo(alias="model_aliases", default=None)


class Team(BaseModel):
    team_id: str

    admins: Optional[List[object]] = None

    blocked: Optional[bool] = None

    budget_duration: Optional[str] = None

    budget_reset_at: Optional[datetime] = None

    created_at: Optional[datetime] = None

    llm_model_table: Optional[TeamLlmModelTable] = None

    max_budget: Optional[float] = None

    max_parallel_requests: Optional[int] = None

    members: Optional[List[object]] = None

    members_with_roles: Optional[List[member.Member]] = None

    metadata: Optional[object] = None

    api_model_id: Optional[int] = FieldInfo(alias="model_id", default=None)

    models: Optional[List[object]] = None

    organization_id: Optional[str] = None

    rpm_limit: Optional[int] = None

    spend: Optional[float] = None

    team_alias: Optional[str] = None

    tpm_limit: Optional[int] = None


class OrganizationUpdateResponse(BaseModel):
    budget_id: str

    created_at: datetime

    created_by: str

    models: List[str]

    updated_at: datetime

    updated_by: str

    llm_budget_table: Optional[LlmBudgetTable] = None
    """Represents user-controllable params for a LLM_BudgetTable record"""

    members: Optional[List[Member]] = None

    metadata: Optional[object] = None

    organization_alias: Optional[str] = None

    organization_id: Optional[str] = None

    spend: Optional[float] = None

    teams: Optional[List[Team]] = None
