# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from __future__ import annotations

from typing import Optional
from typing_extensions import Literal, Required, TypedDict

__all__ = ["MemberParam"]


class MemberParam(TypedDict, total=False):
    role: Required[Literal["admin", "user"]]

    user_email: Optional[str]

    user_id: Optional[str]
