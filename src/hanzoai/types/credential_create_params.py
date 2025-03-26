# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from __future__ import annotations

from typing import Optional
from typing_extensions import Required, TypedDict

__all__ = ["CredentialCreateParams"]


class CredentialCreateParams(TypedDict, total=False):
    credential_info: Required[object]

    credential_name: Required[str]

    credential_values: Optional[object]

    model_id: Optional[str]
