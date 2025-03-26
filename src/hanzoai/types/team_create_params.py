# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from __future__ import annotations

from typing import List, Iterable, Optional
from typing_extensions import Annotated, TypedDict

from .._utils import PropertyInfo
from .member_param import MemberParam

__all__ = ["TeamCreateParams"]


class TeamCreateParams(TypedDict, total=False):
    admins: Iterable[object]

    blocked: bool

    budget_duration: Optional[str]

    guardrails: Optional[List[str]]

    max_budget: Optional[float]

    members: Iterable[object]

    members_with_roles: Iterable[MemberParam]

    metadata: Optional[object]

    model_aliases: Optional[object]

    models: Iterable[object]

    organization_id: Optional[str]

    rpm_limit: Optional[int]

    tags: Optional[Iterable[object]]

    team_alias: Optional[str]

    team_id: Optional[str]

    tpm_limit: Optional[int]

    llm_changed_by: Annotated[str, PropertyInfo(alias="llm-changed-by")]
    """
    The llm-changed-by header enables tracking of actions performed by authorized
    users on behalf of other users, providing an audit trail for accountability
    """
