# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from __future__ import annotations

from typing import List, Iterable, Optional
from typing_extensions import Required, Annotated, TypedDict

from .._utils import PropertyInfo

__all__ = ["TeamUpdateParams"]


class TeamUpdateParams(TypedDict, total=False):
    team_id: Required[str]

    blocked: Optional[bool]

    budget_duration: Optional[str]

    guardrails: Optional[List[str]]

    max_budget: Optional[float]

    metadata: Optional[object]

    model_aliases: Optional[object]

    models: Optional[Iterable[object]]

    organization_id: Optional[str]

    rpm_limit: Optional[int]

    tags: Optional[Iterable[object]]

    team_alias: Optional[str]

    tpm_limit: Optional[int]

    llm_changed_by: Annotated[str, PropertyInfo(alias="llm-changed-by")]
    """
    The llm-changed-by header enables tracking of actions performed by authorized
    users on behalf of other users, providing an audit trail for accountability
    """
