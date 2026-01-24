# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from __future__ import annotations

from typing import Dict, Iterable, Optional
from typing_extensions import Required, TypedDict

from .._types import SequenceNotStr

__all__ = ["OrganizationCreateParams", "ObjectPermission"]


class OrganizationCreateParams(TypedDict, total=False):
    organization_alias: Required[str]

    budget_duration: Optional[str]

    budget_id: Optional[str]

    max_budget: Optional[float]

    max_parallel_requests: Optional[int]

    metadata: Optional[Dict[str, object]]

    model_max_budget: Optional[Dict[str, object]]

    model_rpm_limit: Optional[Dict[str, int]]

    model_tpm_limit: Optional[Dict[str, int]]

    models: Iterable[object]

    object_permission: Optional[ObjectPermission]

    organization_id: Optional[str]

    rpm_limit: Optional[int]

    soft_budget: Optional[float]

    tpm_limit: Optional[int]


class ObjectPermission(TypedDict, total=False):
    agent_access_groups: Optional[SequenceNotStr[str]]

    agents: Optional[SequenceNotStr[str]]

    mcp_access_groups: Optional[SequenceNotStr[str]]

    mcp_servers: Optional[SequenceNotStr[str]]

    mcp_tool_permissions: Optional[Dict[str, SequenceNotStr[str]]]

    vector_stores: Optional[SequenceNotStr[str]]
