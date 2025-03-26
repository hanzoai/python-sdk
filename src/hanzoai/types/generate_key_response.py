# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from typing import List, Optional
from datetime import datetime

from pydantic import Field as FieldInfo

from .._models import BaseModel

__all__ = ["GenerateKeyResponse"]


class GenerateKeyResponse(BaseModel):
    expires: Optional[datetime] = None

    key: str

    token: Optional[str] = None

    aliases: Optional[object] = None

    allowed_cache_controls: Optional[List[object]] = None

    blocked: Optional[bool] = None

    budget_duration: Optional[str] = None

    budget_id: Optional[str] = None

    config: Optional[object] = None

    created_by: Optional[str] = None

    duration: Optional[str] = None

    enforced_params: Optional[List[str]] = None

    guardrails: Optional[List[str]] = None

    key_alias: Optional[str] = None

    key_name: Optional[str] = None

    llm_budget_table: Optional[object] = None

    max_budget: Optional[float] = None

    max_parallel_requests: Optional[int] = None

    metadata: Optional[object] = None

    api_model_max_budget: Optional[object] = FieldInfo(alias="model_max_budget", default=None)

    api_model_rpm_limit: Optional[object] = FieldInfo(alias="model_rpm_limit", default=None)

    api_model_tpm_limit: Optional[object] = FieldInfo(alias="model_tpm_limit", default=None)

    models: Optional[List[object]] = None

    permissions: Optional[object] = None

    rpm_limit: Optional[int] = None

    spend: Optional[float] = None

    tags: Optional[List[str]] = None

    team_id: Optional[str] = None

    token_id: Optional[str] = None

    tpm_limit: Optional[int] = None

    updated_by: Optional[str] = None

    user_id: Optional[str] = None
