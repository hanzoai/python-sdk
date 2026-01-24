# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from typing import Dict, List, Union, Optional
from datetime import datetime
from typing_extensions import Literal

from pydantic import Field as FieldInfo

from .._models import BaseModel

__all__ = ["UserCreateResponse", "AllowedVectorStoreIndex", "ObjectPermission", "RouterSettings"]


class AllowedVectorStoreIndex(BaseModel):
    index_name: str

    index_permissions: List[Literal["read", "write"]]


class ObjectPermission(BaseModel):
    agent_access_groups: Optional[List[str]] = None

    agents: Optional[List[str]] = None

    mcp_access_groups: Optional[List[str]] = None

    mcp_servers: Optional[List[str]] = None

    mcp_tool_permissions: Optional[Dict[str, List[str]]] = None

    vector_stores: Optional[List[str]] = None


class RouterSettings(BaseModel):
    """Set of params that you can modify via `router.update_settings()`."""

    allowed_fails: Optional[int] = None

    context_window_fallbacks: Optional[List[Dict[str, object]]] = None

    cooldown_time: Optional[float] = None

    fallbacks: Optional[List[Dict[str, object]]] = None

    max_retries: Optional[int] = None

    api_model_group_alias: Optional[Dict[str, Union[str, Dict[str, object]]]] = FieldInfo(
        alias="model_group_alias", default=None
    )

    api_model_group_retry_policy: Optional[Dict[str, object]] = FieldInfo(
        alias="model_group_retry_policy", default=None
    )

    num_retries: Optional[int] = None

    retry_after: Optional[float] = None

    routing_strategy: Optional[str] = None

    routing_strategy_args: Optional[Dict[str, object]] = None

    timeout: Optional[float] = None


class UserCreateResponse(BaseModel):
    key: str

    token: Optional[str] = None

    aliases: Optional[Dict[str, object]] = None

    allowed_cache_controls: Optional[List[object]] = None

    allowed_passthrough_routes: Optional[List[object]] = None

    allowed_routes: Optional[List[object]] = None

    allowed_vector_store_indexes: Optional[List[AllowedVectorStoreIndex]] = None

    blocked: Optional[bool] = None

    budget_duration: Optional[str] = None

    budget_id: Optional[str] = None

    config: Optional[Dict[str, object]] = None

    created_at: Optional[datetime] = None

    created_by: Optional[str] = None

    duration: Optional[str] = None

    enforced_params: Optional[List[str]] = None

    expires: Optional[datetime] = None

    guardrails: Optional[List[str]] = None

    key_alias: Optional[str] = None

    key_name: Optional[str] = None

    litellm_budget_table: Optional[object] = None

    max_budget: Optional[float] = None

    max_parallel_requests: Optional[int] = None

    metadata: Optional[Dict[str, object]] = None

    api_model_max_budget: Optional[Dict[str, object]] = FieldInfo(alias="model_max_budget", default=None)

    api_model_rpm_limit: Optional[Dict[str, object]] = FieldInfo(alias="model_rpm_limit", default=None)

    api_model_tpm_limit: Optional[Dict[str, object]] = FieldInfo(alias="model_tpm_limit", default=None)

    models: Optional[List[object]] = None

    object_permission: Optional[ObjectPermission] = None

    organization_id: Optional[str] = None

    permissions: Optional[Dict[str, object]] = None

    prompts: Optional[List[str]] = None

    router_settings: Optional[RouterSettings] = None
    """Set of params that you can modify via `router.update_settings()`."""

    rpm_limit: Optional[int] = None

    rpm_limit_type: Optional[Literal["guaranteed_throughput", "best_effort_throughput", "dynamic"]] = None

    spend: Optional[float] = None

    tags: Optional[List[str]] = None

    team_id: Optional[str] = None

    teams: Optional[List[object]] = None

    token_id: Optional[str] = None

    tpm_limit: Optional[int] = None

    tpm_limit_type: Optional[Literal["guaranteed_throughput", "best_effort_throughput", "dynamic"]] = None

    updated_at: Optional[datetime] = None

    updated_by: Optional[str] = None

    user_alias: Optional[str] = None

    user_email: Optional[str] = None

    user_id: Optional[str] = None

    user_role: Optional[Literal["proxy_admin", "proxy_admin_viewer", "internal_user", "internal_user_viewer"]] = None
