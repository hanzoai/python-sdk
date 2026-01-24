# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from __future__ import annotations

from typing import Dict, List, Iterable, Optional
from typing_extensions import Literal, Required, Annotated, TypedDict

from .._types import SequenceNotStr
from .._utils import PropertyInfo
from .member_param import MemberParam

__all__ = ["TeamCreateParams", "AllowedVectorStoreIndex", "ObjectPermission"]


class TeamCreateParams(TypedDict, total=False):
    admins: Iterable[object]

    allowed_passthrough_routes: Optional[Iterable[object]]

    allowed_vector_store_indexes: Optional[Iterable[AllowedVectorStoreIndex]]

    blocked: bool

    budget_duration: Optional[str]

    guardrails: Optional[SequenceNotStr[str]]

    max_budget: Optional[float]

    members: Iterable[object]

    members_with_roles: Iterable[MemberParam]

    metadata: Optional[Dict[str, object]]

    model_aliases: Optional[Dict[str, object]]

    model_rpm_limit: Optional[Dict[str, int]]

    model_tpm_limit: Optional[Dict[str, int]]

    models: Iterable[object]

    object_permission: Optional[ObjectPermission]

    organization_id: Optional[str]

    prompts: Optional[SequenceNotStr[str]]

    router_settings: Optional[Dict[str, object]]

    rpm_limit: Optional[int]

    rpm_limit_type: Optional[Literal["guaranteed_throughput", "best_effort_throughput"]]

    secret_manager_settings: Optional[Dict[str, object]]

    tags: Optional[Iterable[object]]

    team_alias: Optional[str]

    team_id: Optional[str]

    team_member_budget: Optional[float]

    team_member_key_duration: Optional[str]

    team_member_permissions: Optional[SequenceNotStr[str]]

    team_member_rpm_limit: Optional[int]

    team_member_tpm_limit: Optional[int]

    tpm_limit: Optional[int]

    tpm_limit_type: Optional[Literal["guaranteed_throughput", "best_effort_throughput"]]

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
