# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from typing import List, Optional
from datetime import datetime

from .._models import BaseModel

__all__ = ["OrganizationCreateResponse"]


class OrganizationCreateResponse(BaseModel):
    budget_id: str

    created_at: datetime

    created_by: str

    models: List[str]

    organization_id: str

    updated_at: datetime

    updated_by: str

    metadata: Optional[object] = None

    organization_alias: Optional[str] = None

    spend: Optional[float] = None
