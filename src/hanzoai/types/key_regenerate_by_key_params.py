# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from __future__ import annotations

from typing import List, Iterable, Optional
from typing_extensions import Annotated, TypedDict

from .._utils import PropertyInfo

__all__ = ["KeyRegenerateByKeyParams"]


class KeyRegenerateByKeyParams(TypedDict, total=False):
    aliases: Optional[object]

    allowed_cache_controls: Optional[Iterable[object]]

    blocked: Optional[bool]

    budget_duration: Optional[str]

    budget_id: Optional[str]

    config: Optional[object]

    duration: Optional[str]

    enforced_params: Optional[List[str]]

    guardrails: Optional[List[str]]

    body_key: Annotated[Optional[str], PropertyInfo(alias="key")]

    key_alias: Optional[str]

    max_budget: Optional[float]

    max_parallel_requests: Optional[int]

    metadata: Optional[object]

    model_max_budget: Optional[object]

    model_rpm_limit: Optional[object]

    model_tpm_limit: Optional[object]

    models: Optional[Iterable[object]]

    new_master_key: Optional[str]

    permissions: Optional[object]

    rpm_limit: Optional[int]

    send_invite_email: Optional[bool]

    soft_budget: Optional[float]

    spend: Optional[float]

    tags: Optional[List[str]]

    team_id: Optional[str]

    tpm_limit: Optional[int]

    user_id: Optional[str]

    llm_changed_by: Annotated[str, PropertyInfo(alias="llm-changed-by")]
    """
    The llm-changed-by header enables tracking of actions performed by authorized
    users on behalf of other users, providing an audit trail for accountability
    """
