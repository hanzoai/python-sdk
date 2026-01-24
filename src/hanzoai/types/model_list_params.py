# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from __future__ import annotations

from typing import Optional
from typing_extensions import TypedDict

__all__ = ["ModelListParams"]


class ModelListParams(TypedDict, total=False):
    fallback_type: Optional[str]

    include_metadata: Optional[bool]

    include_model_access_groups: Optional[bool]

    only_model_access_groups: Optional[bool]

    return_wildcard_routes: Optional[bool]

    team_id: Optional[str]
