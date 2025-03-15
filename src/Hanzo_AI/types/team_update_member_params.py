# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from __future__ import annotations

from typing import Optional
from typing_extensions import Literal, Required, TypedDict

__all__ = ["TeamUpdateMemberParams"]


class TeamUpdateMemberParams(TypedDict, total=False):
    team_id: Required[str]

    max_budget_in_team: Optional[float]

    role: Optional[Literal["admin", "user"]]

    user_email: Optional[str]

    user_id: Optional[str]
