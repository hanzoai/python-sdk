# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from typing_extensions import Literal, TypeAlias

__all__ = ["UserRoles"]

UserRoles: TypeAlias = Literal[
    "proxy_admin", "proxy_admin_viewer", "org_admin", "internal_user", "internal_user_viewer", "team", "customer"
]
