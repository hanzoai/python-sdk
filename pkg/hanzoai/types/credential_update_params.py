# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from __future__ import annotations

from typing_extensions import Required, Annotated, TypedDict

from .._utils import PropertyInfo

__all__ = ["CredentialUpdateParams"]


class CredentialUpdateParams(TypedDict, total=False):
    credential_info: Required[object]

    body_credential_name: Required[
        Annotated[str, PropertyInfo(alias="credential_name")]
    ]

    credential_values: Required[object]
