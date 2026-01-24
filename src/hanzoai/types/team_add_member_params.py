# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from __future__ import annotations

from typing import Union, Iterable, Optional
from typing_extensions import Required, TypeAlias, TypedDict

from .member_param import MemberParam

__all__ = ["TeamAddMemberParams", "Member"]


class TeamAddMemberParams(TypedDict, total=False):
    member: Required[Member]
    """Member object or list of member objects to add.

    Each member must include either user_id or user_email, and a role
    """

    team_id: Required[str]
    """The ID of the team to add the member to"""

    max_budget_in_team: Optional[float]
    """Maximum budget allocated to this user within the team.

    If not set, user has unlimited budget within team limits
    """


Member: TypeAlias = Union[Iterable[MemberParam], MemberParam]
