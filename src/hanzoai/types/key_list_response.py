# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from typing import Dict, List, Union, Optional
from datetime import datetime
from typing_extensions import Literal, TypeAlias

from pydantic import Field as FieldInfo

from .member import Member
from .._models import BaseModel

__all__ = ["KeyListResponse", "Key", "KeyUserAPIKeyAuth"]


class KeyUserAPIKeyAuth(BaseModel):
    token: Optional[str] = None

    aliases: Optional[object] = None

    allowed_cache_controls: Optional[List[object]] = None

    allowed_model_region: Optional[Literal["eu", "us"]] = None

    api_key: Optional[str] = None

    blocked: Optional[bool] = None

    budget_duration: Optional[str] = None

    budget_reset_at: Optional[datetime] = None

    config: Optional[object] = None

    created_at: Optional[datetime] = None

    created_by: Optional[str] = None

    end_user_id: Optional[str] = None

    end_user_max_budget: Optional[float] = None

    end_user_rpm_limit: Optional[int] = None

    end_user_tpm_limit: Optional[int] = None

    expires: Union[str, datetime, None] = None

    key_alias: Optional[str] = None

    key_name: Optional[str] = None

    last_refreshed_at: Optional[float] = None

    llm_budget_table: Optional[object] = None

    max_budget: Optional[float] = None

    max_parallel_requests: Optional[int] = None

    metadata: Optional[object] = None

    api_model_max_budget: Optional[object] = FieldInfo(alias="model_max_budget", default=None)

    api_model_spend: Optional[object] = FieldInfo(alias="model_spend", default=None)

    models: Optional[List[object]] = None

    org_id: Optional[str] = None

    parent_otel_span: Optional[object] = None

    permissions: Optional[object] = None

    rpm_limit: Optional[int] = None

    rpm_limit_per_model: Optional[Dict[str, int]] = None

    soft_budget: Optional[float] = None

    soft_budget_cooldown: Optional[bool] = None

    spend: Optional[float] = None

    team_alias: Optional[str] = None

    team_blocked: Optional[bool] = None

    team_id: Optional[str] = None

    team_max_budget: Optional[float] = None

    team_member: Optional[Member] = None

    team_member_spend: Optional[float] = None

    team_metadata: Optional[object] = None

    team_model_aliases: Optional[object] = None

    team_models: Optional[List[object]] = None

    team_rpm_limit: Optional[int] = None

    team_spend: Optional[float] = None

    team_tpm_limit: Optional[int] = None

    tpm_limit: Optional[int] = None

    tpm_limit_per_model: Optional[Dict[str, int]] = None

    updated_at: Optional[datetime] = None

    updated_by: Optional[str] = None

    user_email: Optional[str] = None

    user_id: Optional[str] = None

    user_role: Optional[
        Literal[
            "proxy_admin",
            "proxy_admin_viewer",
            "org_admin",
            "internal_user",
            "internal_user_viewer",
            "team",
            "customer",
        ]
    ] = None
    """
    Admin Roles: PROXY_ADMIN: admin over the platform PROXY_ADMIN_VIEW_ONLY: can
    login, view all own keys, view all spend ORG_ADMIN: admin over a specific
    organization, can create teams, users only within their organization

    Internal User Roles: INTERNAL_USER: can login, view/create/delete their own
    keys, view their spend INTERNAL_USER_VIEW_ONLY: can login, view their own keys,
    view their own spend

    Team Roles: TEAM: used for JWT auth

    Customer Roles: CUSTOMER: External users -> these are customers
    """

    user_rpm_limit: Optional[int] = None

    user_tpm_limit: Optional[int] = None


Key: TypeAlias = Union[str, KeyUserAPIKeyAuth]


class KeyListResponse(BaseModel):
    current_page: Optional[int] = None

    keys: Optional[List[Key]] = None

    total_count: Optional[int] = None

    total_pages: Optional[int] = None
