# Hanzo AI SDK

from __future__ import annotations

from typing import Optional
from typing_extensions import Required, TypedDict

__all__ = ["OrganizationDeleteMemberParams"]


class OrganizationDeleteMemberParams(TypedDict, total=False):
    organization_id: Required[str]

    user_email: Optional[str]

    user_id: Optional[str]
