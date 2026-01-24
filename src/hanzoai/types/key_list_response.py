# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from typing import Dict, List, Union, Optional
from datetime import datetime
from typing_extensions import Literal, TypeAlias

from pydantic import Field as FieldInfo

from .member import Member
from .._models import BaseModel
from .user_roles import UserRoles

__all__ = [
    "KeyListResponse",
    "Key",
    "KeyUserAPIKeyAuth",
    "KeyUserAPIKeyAuthObjectPermission",
    "KeyLiteLlmDeletedVerificationToken",
    "KeyLiteLlmDeletedVerificationTokenObjectPermission",
]


class KeyUserAPIKeyAuthObjectPermission(BaseModel):
    """Represents a LiteLLM_ObjectPermissionTable record"""

    object_permission_id: str

    agent_access_groups: Optional[List[str]] = None

    agents: Optional[List[str]] = None

    mcp_access_groups: Optional[List[str]] = None

    mcp_servers: Optional[List[str]] = None

    mcp_tool_permissions: Optional[Dict[str, List[str]]] = None

    vector_stores: Optional[List[str]] = None


class KeyUserAPIKeyAuth(BaseModel):
    """Return the row in the db"""

    token: Optional[str] = None

    aliases: Optional[Dict[str, object]] = None

    allowed_cache_controls: Optional[List[object]] = None

    allowed_model_region: Optional[Literal["eu", "us"]] = None

    allowed_routes: Optional[List[object]] = None

    api_key: Optional[str] = None

    auto_rotate: Optional[bool] = None

    blocked: Optional[bool] = None

    budget_duration: Optional[str] = None

    budget_reset_at: Optional[datetime] = None

    config: Optional[Dict[str, object]] = None

    created_at: Optional[datetime] = None

    created_by: Optional[str] = None

    end_user_id: Optional[str] = None

    end_user_max_budget: Optional[float] = None

    end_user_rpm_limit: Optional[int] = None

    end_user_tpm_limit: Optional[int] = None

    expires: Union[str, datetime, None] = None

    key_alias: Optional[str] = None

    key_name: Optional[str] = None

    key_rotation_at: Optional[datetime] = None

    last_refreshed_at: Optional[float] = None

    last_rotation_at: Optional[datetime] = None

    litellm_budget_table: Optional[Dict[str, object]] = None

    max_budget: Optional[float] = None

    max_parallel_requests: Optional[int] = None

    metadata: Optional[Dict[str, object]] = None

    api_model_max_budget: Optional[Dict[str, object]] = FieldInfo(alias="model_max_budget", default=None)

    api_model_spend: Optional[Dict[str, object]] = FieldInfo(alias="model_spend", default=None)

    models: Optional[List[object]] = None

    object_permission: Optional[KeyUserAPIKeyAuthObjectPermission] = None
    """Represents a LiteLLM_ObjectPermissionTable record"""

    object_permission_id: Optional[str] = None

    org_id: Optional[str] = None

    organization_max_budget: Optional[float] = None

    organization_metadata: Optional[Dict[str, object]] = None

    organization_rpm_limit: Optional[int] = None

    organization_tpm_limit: Optional[int] = None

    parent_otel_span: Optional[object] = None

    permissions: Optional[Dict[str, object]] = None

    request_route: Optional[str] = None

    rotation_count: Optional[int] = None

    rotation_interval: Optional[str] = None

    router_settings: Optional[Dict[str, object]] = None

    rpm_limit: Optional[int] = None

    rpm_limit_per_model: Optional[Dict[str, int]] = None

    soft_budget: Optional[float] = None

    soft_budget_cooldown: Optional[bool] = None

    spend: Optional[float] = None

    team_alias: Optional[str] = None

    team_blocked: Optional[bool] = None

    team_id: Optional[str] = None

    team_max_budget: Optional[float] = None

    team_member: Optional[Member] = None

    team_member_rpm_limit: Optional[int] = None

    team_member_spend: Optional[float] = None

    team_member_tpm_limit: Optional[int] = None

    team_metadata: Optional[Dict[str, object]] = None

    team_model_aliases: Optional[Dict[str, object]] = None

    team_models: Optional[List[object]] = None

    team_object_permission_id: Optional[str] = None

    team_rpm_limit: Optional[int] = None

    team_spend: Optional[float] = None

    team_tpm_limit: Optional[int] = None

    tpm_limit: Optional[int] = None

    tpm_limit_per_model: Optional[Dict[str, int]] = None

    updated_at: Optional[datetime] = None

    updated_by: Optional[str] = None

    user: Optional[object] = None

    user_email: Optional[str] = None

    user_id: Optional[str] = None

    user_max_budget: Optional[float] = None

    user_role: Optional[UserRoles] = None
    """
    Admin Roles: PROXY_ADMIN: admin over the platform PROXY_ADMIN_VIEW_ONLY: can
    login, view all own keys, view all spend ORG_ADMIN: admin over a specific
    organization, can create teams, users only within their organization

    Internal User Roles: INTERNAL_USER: can login, view/create/delete their own
    keys, view their spend INTERNAL_USER_VIEW_ONLY: can login, view their own keys,
    view their own spend

    Team Roles: TEAM: used for JWT auth

    Customer Roles: CUSTOMER: External users -> these are customers
    """

    user_rpm_limit: Optional[int] = None

    user_spend: Optional[float] = None

    user_tpm_limit: Optional[int] = None


class KeyLiteLlmDeletedVerificationTokenObjectPermission(BaseModel):
    """Represents a LiteLLM_ObjectPermissionTable record"""

    object_permission_id: str

    agent_access_groups: Optional[List[str]] = None

    agents: Optional[List[str]] = None

    mcp_access_groups: Optional[List[str]] = None

    mcp_servers: Optional[List[str]] = None

    mcp_tool_permissions: Optional[Dict[str, List[str]]] = None

    vector_stores: Optional[List[str]] = None


class KeyLiteLlmDeletedVerificationToken(BaseModel):
    """Recording of deleted keys for audit purposes.

    Mirrors LiteLLM_VerificationToken
    plus metadata captured at deletion time.
    """

    id: Optional[str] = None

    token: Optional[str] = None

    aliases: Optional[Dict[str, object]] = None

    allowed_cache_controls: Optional[List[object]] = None

    allowed_routes: Optional[List[object]] = None

    auto_rotate: Optional[bool] = None

    blocked: Optional[bool] = None

    budget_duration: Optional[str] = None

    budget_reset_at: Optional[datetime] = None

    config: Optional[Dict[str, object]] = None

    created_at: Optional[datetime] = None

    created_by: Optional[str] = None

    deleted_at: Optional[datetime] = None

    deleted_by: Optional[str] = None

    deleted_by_api_key: Optional[str] = None

    expires: Union[str, datetime, None] = None

    key_alias: Optional[str] = None

    key_name: Optional[str] = None

    key_rotation_at: Optional[datetime] = None

    last_rotation_at: Optional[datetime] = None

    litellm_budget_table: Optional[Dict[str, object]] = None

    litellm_changed_by: Optional[str] = None

    max_budget: Optional[float] = None

    max_parallel_requests: Optional[int] = None

    metadata: Optional[Dict[str, object]] = None

    api_model_max_budget: Optional[Dict[str, object]] = FieldInfo(alias="model_max_budget", default=None)

    api_model_spend: Optional[Dict[str, object]] = FieldInfo(alias="model_spend", default=None)

    models: Optional[List[object]] = None

    object_permission: Optional[KeyLiteLlmDeletedVerificationTokenObjectPermission] = None
    """Represents a LiteLLM_ObjectPermissionTable record"""

    object_permission_id: Optional[str] = None

    org_id: Optional[str] = None

    permissions: Optional[Dict[str, object]] = None

    rotation_count: Optional[int] = None

    rotation_interval: Optional[str] = None

    router_settings: Optional[Dict[str, object]] = None

    rpm_limit: Optional[int] = None

    soft_budget_cooldown: Optional[bool] = None

    spend: Optional[float] = None

    team_id: Optional[str] = None

    tpm_limit: Optional[int] = None

    updated_at: Optional[datetime] = None

    updated_by: Optional[str] = None

    user_id: Optional[str] = None


Key: TypeAlias = Union[str, KeyUserAPIKeyAuth, KeyLiteLlmDeletedVerificationToken]


class KeyListResponse(BaseModel):
    current_page: Optional[int] = None

    keys: Optional[List[Key]] = None

    total_count: Optional[int] = None

    total_pages: Optional[int] = None
