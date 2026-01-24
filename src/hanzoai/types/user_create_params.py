# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from __future__ import annotations

from typing import Dict, Union, Iterable, Optional
from typing_extensions import Literal, Required, TypedDict

from .._types import SequenceNotStr

__all__ = ["UserCreateParams", "ObjectPermission", "TeamsUnionMember1"]


class UserCreateParams(TypedDict, total=False):
    aliases: Optional[Dict[str, object]]

    allowed_cache_controls: Optional[Iterable[object]]

    auto_create_key: bool

    blocked: Optional[bool]

    budget_duration: Optional[str]

    config: Optional[Dict[str, object]]

    duration: Optional[str]

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

    organizations: Optional[SequenceNotStr[str]]

    permissions: Optional[Dict[str, object]]

    prompts: Optional[SequenceNotStr[str]]

    rpm_limit: Optional[int]

    send_invite_email: Optional[bool]

    spend: Optional[float]

    sso_user_id: Optional[str]

    team_id: Optional[str]

    teams: Union[SequenceNotStr[str], Iterable[TeamsUnionMember1], None]

    tpm_limit: Optional[int]

    user_alias: Optional[str]

    user_email: Optional[str]

    user_id: Optional[str]

    user_role: Optional[Literal["proxy_admin", "proxy_admin_viewer", "internal_user", "internal_user_viewer"]]


class ObjectPermission(TypedDict, total=False):
    agent_access_groups: Optional[SequenceNotStr[str]]

    agents: Optional[SequenceNotStr[str]]

    mcp_access_groups: Optional[SequenceNotStr[str]]

    mcp_servers: Optional[SequenceNotStr[str]]

    mcp_tool_permissions: Optional[Dict[str, SequenceNotStr[str]]]

    vector_stores: Optional[SequenceNotStr[str]]


class TeamsUnionMember1(TypedDict, total=False):
    team_id: Required[str]

    max_budget_in_team: Optional[float]

    user_role: Literal["user", "admin"]
