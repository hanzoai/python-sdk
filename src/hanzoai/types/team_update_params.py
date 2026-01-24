# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from __future__ import annotations

from typing import Dict, List, Iterable, Optional
from typing_extensions import Literal, Required, Annotated, TypedDict

from .._types import SequenceNotStr
from .._utils import PropertyInfo

__all__ = ["TeamUpdateParams", "AllowedVectorStoreIndex", "ObjectPermission"]


class TeamUpdateParams(TypedDict, total=False):
    team_id: Required[str]

    allowed_passthrough_routes: Optional[Iterable[object]]

    allowed_vector_store_indexes: Optional[Iterable[AllowedVectorStoreIndex]]

    blocked: Optional[bool]

    budget_duration: Optional[str]

    guardrails: Optional[SequenceNotStr[str]]

    max_budget: Optional[float]

    metadata: Optional[Dict[str, object]]

    model_aliases: Optional[Dict[str, object]]

    model_rpm_limit: Optional[Dict[str, int]]

    model_tpm_limit: Optional[Dict[str, int]]

    models: Optional[Iterable[object]]

    object_permission: Optional[ObjectPermission]

    organization_id: Optional[str]

    prompts: Optional[SequenceNotStr[str]]

    router_settings: Optional[Dict[str, object]]

    rpm_limit: Optional[int]

    secret_manager_settings: Optional[Dict[str, object]]

    tags: Optional[Iterable[object]]

    team_alias: Optional[str]

    team_member_budget: Optional[float]

    team_member_budget_duration: Optional[str]

    team_member_key_duration: Optional[str]

    team_member_rpm_limit: Optional[int]

    team_member_tpm_limit: Optional[int]

    tpm_limit: Optional[int]

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
