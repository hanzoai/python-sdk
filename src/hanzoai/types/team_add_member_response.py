# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from typing import Dict, List, Union, Optional
from datetime import datetime

from pydantic import Field as FieldInfo

from .member import Member
from .._models import BaseModel
from .budget_table import BudgetTable
from .organization_membership_table import OrganizationMembershipTable

__all__ = [
    "TeamAddMemberResponse",
    "UpdatedTeamMembership",
    "UpdatedUser",
    "UpdatedUserObjectPermission",
    "LitellmModelTable",
    "ObjectPermission",
]


class UpdatedTeamMembership(BaseModel):
    litellm_budget_table: Optional[BudgetTable] = None
    """Represents user-controllable params for a LiteLLM_BudgetTable record"""

    team_id: str

    user_id: str

    budget_id: Optional[str] = None

    spend: Optional[float] = None


class UpdatedUserObjectPermission(BaseModel):
    """Represents a LiteLLM_ObjectPermissionTable record"""

    object_permission_id: str

    agent_access_groups: Optional[List[str]] = None

    agents: Optional[List[str]] = None

    mcp_access_groups: Optional[List[str]] = None

    mcp_servers: Optional[List[str]] = None

    mcp_tool_permissions: Optional[Dict[str, List[str]]] = None

    vector_stores: Optional[List[str]] = None


class UpdatedUser(BaseModel):
    user_id: str

    budget_duration: Optional[str] = None

    budget_reset_at: Optional[datetime] = None

    created_at: Optional[datetime] = None

    max_budget: Optional[float] = None

    metadata: Optional[Dict[str, object]] = None

    api_model_max_budget: Optional[Dict[str, object]] = FieldInfo(alias="model_max_budget", default=None)

    api_model_spend: Optional[Dict[str, object]] = FieldInfo(alias="model_spend", default=None)

    models: Optional[List[object]] = None

    object_permission: Optional[UpdatedUserObjectPermission] = None
    """Represents a LiteLLM_ObjectPermissionTable record"""

    organization_memberships: Optional[List[OrganizationMembershipTable]] = None

    rpm_limit: Optional[int] = None

    spend: Optional[float] = None

    sso_user_id: Optional[str] = None

    teams: Optional[List[str]] = None

    tpm_limit: Optional[int] = None

    updated_at: Optional[datetime] = None

    user_alias: Optional[str] = None

    user_email: Optional[str] = None

    user_role: Optional[str] = None


class LitellmModelTable(BaseModel):
    created_by: str

    updated_by: str

    id: Optional[int] = None

    api_model_aliases: Union[Dict[str, object], str, None] = FieldInfo(alias="model_aliases", default=None)

    team: Optional[object] = None


class ObjectPermission(BaseModel):
    """Represents a LiteLLM_ObjectPermissionTable record"""

    object_permission_id: str

    agent_access_groups: Optional[List[str]] = None

    agents: Optional[List[str]] = None

    mcp_access_groups: Optional[List[str]] = None

    mcp_servers: Optional[List[str]] = None

    mcp_tool_permissions: Optional[Dict[str, List[str]]] = None

    vector_stores: Optional[List[str]] = None


class TeamAddMemberResponse(BaseModel):
    team_id: str

    updated_team_memberships: List[UpdatedTeamMembership]

    updated_users: List[UpdatedUser]

    admins: Optional[List[object]] = None

    blocked: Optional[bool] = None

    budget_duration: Optional[str] = None

    budget_reset_at: Optional[datetime] = None

    created_at: Optional[datetime] = None

    litellm_model_table: Optional[LitellmModelTable] = None

    max_budget: Optional[float] = None

    max_parallel_requests: Optional[int] = None

    members: Optional[List[object]] = None

    members_with_roles: Optional[List[Member]] = None

    metadata: Optional[Dict[str, object]] = None

    api_model_id: Optional[int] = FieldInfo(alias="model_id", default=None)

    models: Optional[List[object]] = None

    object_permission: Optional[ObjectPermission] = None
    """Represents a LiteLLM_ObjectPermissionTable record"""

    object_permission_id: Optional[str] = None

    organization_id: Optional[str] = None

    router_settings: Optional[Dict[str, object]] = None

    rpm_limit: Optional[int] = None

    spend: Optional[float] = None

    team_alias: Optional[str] = None

    team_member_permissions: Optional[List[str]] = None

    tpm_limit: Optional[int] = None

    updated_at: Optional[datetime] = None
