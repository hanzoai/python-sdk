# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from typing import List, Union, Optional
from datetime import datetime

from pydantic import Field as FieldInfo

from .._models import BaseModel

__all__ = ["KeyBlockResponse"]


class KeyBlockResponse(BaseModel):
    token: Optional[str] = None

    aliases: Optional[object] = None

    allowed_cache_controls: Optional[List[object]] = None

    blocked: Optional[bool] = None

    budget_duration: Optional[str] = None

    budget_reset_at: Optional[datetime] = None

    config: Optional[object] = None

    created_at: Optional[datetime] = None

    created_by: Optional[str] = None

    expires: Union[str, datetime, None] = None

    key_alias: Optional[str] = None

    key_name: Optional[str] = None

    llm_budget_table: Optional[object] = None

    max_budget: Optional[float] = None

    max_parallel_requests: Optional[int] = None

    metadata: Optional[object] = None

    api_model_max_budget: Optional[object] = FieldInfo(alias="model_max_budget", default=None)

    api_model_spend: Optional[object] = FieldInfo(alias="model_spend", default=None)

    models: Optional[List[object]] = None

    org_id: Optional[str] = None

    permissions: Optional[object] = None

    rpm_limit: Optional[int] = None

    soft_budget_cooldown: Optional[bool] = None

    spend: Optional[float] = None

    team_id: Optional[str] = None

    tpm_limit: Optional[int] = None

    updated_at: Optional[datetime] = None

    updated_by: Optional[str] = None

    user_id: Optional[str] = None
