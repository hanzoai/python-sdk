# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from typing import List
from typing_extensions import TypeAlias

from .organization_table_with_members import OrganizationTableWithMembers

__all__ = ["OrganizationDeleteResponse"]

OrganizationDeleteResponse: TypeAlias = List[OrganizationTableWithMembers]
