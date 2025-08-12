# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from typing import List, Optional
from datetime import datetime

from pydantic import Field as FieldInfo

from .._models import BaseModel
from .organization_membership_table import OrganizationMembershipTable

__all__ = ["HanzoUserTable"]


class HanzoUserTable(BaseModel):
    user_id: str

    budget_duration: Optional[str] = None

    budget_reset_at: Optional[datetime] = None

    max_budget: Optional[float] = None

    metadata: Optional[object] = None

    api_model_max_budget: Optional[object] = FieldInfo(
        alias="model_max_budget", default=None
    )

    api_model_spend: Optional[object] = FieldInfo(alias="model_spend", default=None)

    models: Optional[List[object]] = None

    organization_memberships: Optional[List[OrganizationMembershipTable]] = None

    rpm_limit: Optional[int] = None

    spend: Optional[float] = None

    sso_user_id: Optional[str] = None

    teams: Optional[List[str]] = None

    tpm_limit: Optional[int] = None

    user_email: Optional[str] = None

    user_role: Optional[str] = None
