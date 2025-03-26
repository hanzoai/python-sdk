# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from __future__ import annotations

from typing import List, Union, Iterable, Optional
from datetime import datetime
from typing_extensions import Required, Annotated, TypedDict

from .._utils import PropertyInfo

__all__ = ["KeyUpdateParams"]


class KeyUpdateParams(TypedDict, total=False):
    key: Required[str]

    aliases: Optional[object]

    allowed_cache_controls: Optional[Iterable[object]]

    blocked: Optional[bool]

    budget_duration: Optional[str]

    budget_id: Optional[str]

    config: Optional[object]

    duration: Optional[str]

    enforced_params: Optional[List[str]]

    guardrails: Optional[List[str]]

    key_alias: Optional[str]

    max_budget: Optional[float]

    max_parallel_requests: Optional[int]

    metadata: Optional[object]

    model_max_budget: Optional[object]

    model_rpm_limit: Optional[object]

    model_tpm_limit: Optional[object]

    models: Optional[Iterable[object]]

    permissions: Optional[object]

    rpm_limit: Optional[int]

    spend: Optional[float]

    tags: Optional[List[str]]

    team_id: Optional[str]

    temp_budget_expiry: Annotated[Union[str, datetime, None], PropertyInfo(format="iso8601")]

    temp_budget_increase: Optional[float]

    tpm_limit: Optional[int]

    user_id: Optional[str]

    llm_changed_by: Annotated[str, PropertyInfo(alias="llm-changed-by")]
    """
    The llm-changed-by header enables tracking of actions performed by authorized
    users on behalf of other users, providing an audit trail for accountability
    """
