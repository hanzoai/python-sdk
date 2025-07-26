# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from __future__ import annotations

from typing import Union, Iterable, Optional
from typing_extensions import Required, TypeAlias, TypedDict

from .org_member_param import OrgMemberParam

__all__ = ["OrganizationAddMemberParams", "Member"]


class OrganizationAddMemberParams(TypedDict, total=False):
    member: Required[Member]

    organization_id: Required[str]

    max_budget_in_organization: Optional[float]


Member: TypeAlias = Union[Iterable[OrgMemberParam], OrgMemberParam]
