# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from __future__ import annotations

from typing import Optional
from typing_extensions import Literal, Required, TypedDict

__all__ = ["OrgMemberParam"]


class OrgMemberParam(TypedDict, total=False):
    role: Required[Literal["org_admin", "internal_user", "internal_user_viewer"]]

    user_email: Optional[str]

    user_id: Optional[str]
