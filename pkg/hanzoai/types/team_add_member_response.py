# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from typing import List, Optional
from datetime import datetime

from pydantic import Field as FieldInfo

from .member import Member
from .._models import BaseModel
from .budget_table import BudgetTable
from .lite_llm_user_table import HanzoUserTable
from .lite_llm_model_table import HanzoModelTable

__all__ = ["TeamAddMemberResponse", "UpdatedTeamMembership"]


class UpdatedTeamMembership(BaseModel):
    budget_id: str

    hanzo_budget_table: Optional[BudgetTable] = None
    """Represents user-controllable params for a Hanzo_BudgetTable record"""

    team_id: str

    user_id: str


class TeamAddMemberResponse(BaseModel):
    team_id: str

    updated_team_memberships: List[UpdatedTeamMembership]

    updated_users: List[HanzoUserTable]

    admins: Optional[List[object]] = None

    blocked: Optional[bool] = None

    budget_duration: Optional[str] = None

    budget_reset_at: Optional[datetime] = None

    created_at: Optional[datetime] = None

    hanzo_model_table: Optional[HanzoModelTable] = None

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
