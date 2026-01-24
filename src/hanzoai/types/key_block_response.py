# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from typing import Dict, List, Union, Optional
from datetime import datetime

from pydantic import Field as FieldInfo

from .._models import BaseModel

__all__ = ["KeyBlockResponse", "ObjectPermission"]


class ObjectPermission(BaseModel):
    """Represents a LiteLLM_ObjectPermissionTable record"""

    object_permission_id: str

    agent_access_groups: Optional[List[str]] = None

    agents: Optional[List[str]] = None

    mcp_access_groups: Optional[List[str]] = None

    mcp_servers: Optional[List[str]] = None

    mcp_tool_permissions: Optional[Dict[str, List[str]]] = None

    vector_stores: Optional[List[str]] = None


class KeyBlockResponse(BaseModel):
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

    expires: Union[str, datetime, None] = None

    key_alias: Optional[str] = None

    key_name: Optional[str] = None

    key_rotation_at: Optional[datetime] = None

    last_rotation_at: Optional[datetime] = None

    litellm_budget_table: Optional[Dict[str, object]] = None

    max_budget: Optional[float] = None

    max_parallel_requests: Optional[int] = None

    metadata: Optional[Dict[str, object]] = None

    api_model_max_budget: Optional[Dict[str, object]] = FieldInfo(alias="model_max_budget", default=None)

    api_model_spend: Optional[Dict[str, object]] = FieldInfo(alias="model_spend", default=None)

    models: Optional[List[object]] = None

    object_permission: Optional[ObjectPermission] = None
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
