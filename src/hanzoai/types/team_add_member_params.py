# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from __future__ import annotations

from typing import Union, Iterable, Optional
from typing_extensions import Required, TypeAlias, TypedDict

from .member_param import MemberParam

__all__ = ["TeamAddMemberParams", "Member"]


class TeamAddMemberParams(TypedDict, total=False):
    member: Required[Member]

    team_id: Required[str]

    max_budget_in_team: Optional[float]


Member: TypeAlias = Union[Iterable[MemberParam], MemberParam]
