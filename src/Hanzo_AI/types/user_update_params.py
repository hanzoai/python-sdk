# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from __future__ import annotations

from typing import List, Iterable, Optional
from typing_extensions import Literal, TypedDict

__all__ = ["UserUpdateParams"]


class UserUpdateParams(TypedDict, total=False):
    aliases: Optional[object]

    allowed_cache_controls: Optional[Iterable[object]]

    blocked: Optional[bool]

    budget_duration: Optional[str]

    config: Optional[object]

    duration: Optional[str]

    guardrails: Optional[List[str]]

    key_alias: Optional[str]

    max_budget: Optional[float]

    max_parallel_requests: Optional[int]

    metadata: Optional[object]

    model_max_budget: Optional[object]

    model_rpm_limit: Optional[object]

    model_tpm_limit: Optional[object]

    models: Optional[Iterable[object]]

    password: Optional[str]

    permissions: Optional[object]

    rpm_limit: Optional[int]

    spend: Optional[float]

    team_id: Optional[str]

    tpm_limit: Optional[int]

    user_email: Optional[str]

    user_id: Optional[str]

    user_role: Optional[Literal["proxy_admin", "proxy_admin_viewer", "internal_user", "internal_user_viewer"]]
