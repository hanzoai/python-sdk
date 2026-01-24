# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from __future__ import annotations

from typing import Dict, List, Union, Iterable, Optional
from datetime import datetime
from typing_extensions import Literal, Required, Annotated, TypedDict

from .._types import SequenceNotStr
from .._utils import PropertyInfo

__all__ = ["KeyUpdateParams", "AllowedVectorStoreIndex", "ObjectPermission", "RouterSettings"]


class KeyUpdateParams(TypedDict, total=False):
    key: Required[str]

    aliases: Optional[Dict[str, object]]

    allowed_cache_controls: Optional[Iterable[object]]

    allowed_passthrough_routes: Optional[Iterable[object]]

    allowed_routes: Optional[Iterable[object]]

    allowed_vector_store_indexes: Optional[Iterable[AllowedVectorStoreIndex]]

    auto_rotate: Optional[bool]

    blocked: Optional[bool]

    budget_duration: Optional[str]

    budget_id: Optional[str]

    config: Optional[Dict[str, object]]

    duration: Optional[str]

    enforced_params: Optional[SequenceNotStr[str]]

    guardrails: Optional[SequenceNotStr[str]]

    key_alias: Optional[str]

    max_budget: Optional[float]

    max_parallel_requests: Optional[int]

    metadata: Optional[Dict[str, object]]

    model_max_budget: Optional[Dict[str, object]]

    model_rpm_limit: Optional[Dict[str, object]]

    model_tpm_limit: Optional[Dict[str, object]]

    models: Optional[Iterable[object]]

    object_permission: Optional[ObjectPermission]

    permissions: Optional[Dict[str, object]]

    prompts: Optional[SequenceNotStr[str]]

    rotation_interval: Optional[str]

    router_settings: Optional[RouterSettings]
    """Set of params that you can modify via `router.update_settings()`."""

    rpm_limit: Optional[int]

    rpm_limit_type: Optional[Literal["guaranteed_throughput", "best_effort_throughput", "dynamic"]]

    spend: Optional[float]

    tags: Optional[SequenceNotStr[str]]

    team_id: Optional[str]

    temp_budget_expiry: Annotated[Union[str, datetime, None], PropertyInfo(format="iso8601")]

    temp_budget_increase: Optional[float]

    tpm_limit: Optional[int]

    tpm_limit_type: Optional[Literal["guaranteed_throughput", "best_effort_throughput", "dynamic"]]

    user_id: Optional[str]

    litellm_changed_by: Annotated[str, PropertyInfo(alias="litellm-changed-by")]
    """
    The litellm-changed-by header enables tracking of actions performed by
    authorized users on behalf of other users, providing an audit trail for
    accountability
    """


class AllowedVectorStoreIndex(TypedDict, total=False):
    index_name: Required[str]

    index_permissions: Required[List[Literal["read", "write"]]]


class ObjectPermission(TypedDict, total=False):
    agent_access_groups: Optional[SequenceNotStr[str]]

    agents: Optional[SequenceNotStr[str]]

    mcp_access_groups: Optional[SequenceNotStr[str]]

    mcp_servers: Optional[SequenceNotStr[str]]

    mcp_tool_permissions: Optional[Dict[str, SequenceNotStr[str]]]

    vector_stores: Optional[SequenceNotStr[str]]


class RouterSettings(TypedDict, total=False):
    """Set of params that you can modify via `router.update_settings()`."""

    allowed_fails: Optional[int]

    context_window_fallbacks: Optional[Iterable[Dict[str, object]]]

    cooldown_time: Optional[float]

    fallbacks: Optional[Iterable[Dict[str, object]]]

    max_retries: Optional[int]

    model_group_alias: Optional[Dict[str, Union[str, Dict[str, object]]]]

    model_group_retry_policy: Optional[Dict[str, object]]

    num_retries: Optional[int]

    retry_after: Optional[float]

    routing_strategy: Optional[str]

    routing_strategy_args: Optional[Dict[str, object]]

    timeout: Optional[float]
