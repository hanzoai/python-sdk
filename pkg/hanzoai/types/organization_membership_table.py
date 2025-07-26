# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from typing import Optional
from datetime import datetime

from .._models import BaseModel
from .budget_table import BudgetTable

__all__ = ["OrganizationMembershipTable"]


class OrganizationMembershipTable(BaseModel):
    created_at: datetime

    organization_id: str

    updated_at: datetime

    user_id: str

    budget_id: Optional[str] = None

    hanzo_budget_table: Optional[BudgetTable] = None
    """Represents user-controllable params for a Hanzo_BudgetTable record"""

    spend: Optional[float] = None

    user: Optional[object] = None

    user_role: Optional[str] = None
