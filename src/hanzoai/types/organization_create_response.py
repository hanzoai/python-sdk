# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from typing import Dict, List, Optional
from datetime import datetime

from pydantic import Field as FieldInfo

from .._models import BaseModel
from .budget_table import BudgetTable
from .organization_membership_table import OrganizationMembershipTable

__all__ = ["OrganizationCreateResponse", "ObjectPermission", "User", "UserObjectPermission"]


class ObjectPermission(BaseModel):
    """Represents a LiteLLM_ObjectPermissionTable record"""

    object_permission_id: str

    agent_access_groups: Optional[List[str]] = None

    agents: Optional[List[str]] = None

    mcp_access_groups: Optional[List[str]] = None

    mcp_servers: Optional[List[str]] = None

    mcp_tool_permissions: Optional[Dict[str, List[str]]] = None

    vector_stores: Optional[List[str]] = None


class UserObjectPermission(BaseModel):
    """Represents a LiteLLM_ObjectPermissionTable record"""

    object_permission_id: str

    agent_access_groups: Optional[List[str]] = None

    agents: Optional[List[str]] = None

    mcp_access_groups: Optional[List[str]] = None

    mcp_servers: Optional[List[str]] = None

    mcp_tool_permissions: Optional[Dict[str, List[str]]] = None

    vector_stores: Optional[List[str]] = None


class User(BaseModel):
    user_id: str

    budget_duration: Optional[str] = None

    budget_reset_at: Optional[datetime] = None

    created_at: Optional[datetime] = None

    max_budget: Optional[float] = None

    metadata: Optional[Dict[str, object]] = None

    api_model_max_budget: Optional[Dict[str, object]] = FieldInfo(alias="model_max_budget", default=None)

    api_model_spend: Optional[Dict[str, object]] = FieldInfo(alias="model_spend", default=None)

    models: Optional[List[object]] = None

    object_permission: Optional[UserObjectPermission] = None
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


class OrganizationCreateResponse(BaseModel):
    budget_id: str

    created_at: datetime

    created_by: str

    models: List[str]

    organization_id: str

    updated_at: datetime

    updated_by: str

    litellm_budget_table: Optional[BudgetTable] = None
    """Represents user-controllable params for a LiteLLM_BudgetTable record"""

    metadata: Optional[Dict[str, object]] = None

    object_permission: Optional[ObjectPermission] = None
    """Represents a LiteLLM_ObjectPermissionTable record"""

    object_permission_id: Optional[str] = None

    organization_alias: Optional[str] = None

    spend: Optional[float] = None

    users: Optional[List[User]] = None
