# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from __future__ import annotations

from typing import Optional
from typing_extensions import Literal, Required, TypedDict

__all__ = ["OrganizationUpdateMemberParams"]


class OrganizationUpdateMemberParams(TypedDict, total=False):
    organization_id: Required[str]

    max_budget_in_organization: Optional[float]

    role: Optional[
        Literal[
            "proxy_admin",
            "proxy_admin_viewer",
            "org_admin",
            "internal_user",
            "internal_user_viewer",
            "team",
            "customer",
        ]
    ]
    """
    Admin Roles: PROXY_ADMIN: admin over the platform PROXY_ADMIN_VIEW_ONLY: can
    login, view all own keys, view all spend ORG_ADMIN: admin over a specific
    organization, can create teams, users only within their organization

    Internal User Roles: INTERNAL_USER: can login, view/create/delete their own
    keys, view their spend INTERNAL_USER_VIEW_ONLY: can login, view their own keys,
    view their own spend

    Team Roles: TEAM: used for JWT auth

    Customer Roles: CUSTOMER: External users -> these are customers
    """

    user_email: Optional[str]

    user_id: Optional[str]
