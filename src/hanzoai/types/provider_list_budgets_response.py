# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from typing import Dict, Optional

from .._models import BaseModel

__all__ = ["ProviderListBudgetsResponse", "Providers"]


class Providers(BaseModel):
    """Configuration for a single provider's budget settings"""

    budget_limit: Optional[float] = None

    time_period: Optional[str] = None

    budget_reset_at: Optional[str] = None

    spend: Optional[float] = None


class ProviderListBudgetsResponse(BaseModel):
    """
    Complete provider budget configuration and status.
    Maps provider names to their budget configs.
    """

    providers: Optional[Dict[str, Providers]] = None
