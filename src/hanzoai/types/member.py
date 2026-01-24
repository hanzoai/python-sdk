# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from typing import Optional
from typing_extensions import Literal

from .._models import BaseModel

__all__ = ["Member"]


class Member(BaseModel):
    role: Literal["admin", "user"]
    """The role of the user within the team.

    'admin' users can manage team settings and members, 'user' is a regular team
    member
    """

    user_email: Optional[str] = None
    """The email address of the user to add.

    Either user_id or user_email must be provided
    """

    user_id: Optional[str] = None
    """The unique ID of the user to add. Either user_id or user_email must be provided"""
