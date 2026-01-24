# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from __future__ import annotations

from typing import Optional
from typing_extensions import Literal, Required, TypedDict

__all__ = ["MemberParam"]


class MemberParam(TypedDict, total=False):
    role: Required[Literal["admin", "user"]]
    """The role of the user within the team.

    'admin' users can manage team settings and members, 'user' is a regular team
    member
    """

    user_email: Optional[str]
    """The email address of the user to add.

    Either user_id or user_email must be provided
    """

    user_id: Optional[str]
    """The unique ID of the user to add. Either user_id or user_email must be provided"""
