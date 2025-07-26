# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from typing import List

from .._models import BaseModel
from .lite_llm_user_table import HanzoUserTable
from .organization_membership_table import OrganizationMembershipTable

__all__ = ["OrganizationAddMemberResponse"]


class OrganizationAddMemberResponse(BaseModel):
    organization_id: str

    updated_organization_memberships: List[OrganizationMembershipTable]

    updated_users: List[HanzoUserTable]
