# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from typing import Optional

from .._models import BaseModel

__all__ = ["TeamUpdateMemberResponse"]


class TeamUpdateMemberResponse(BaseModel):
    team_id: str

    user_id: str

    max_budget_in_team: Optional[float] = None

    user_email: Optional[str] = None
