# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from __future__ import annotations

from typing import Optional
from typing_extensions import TypedDict

__all__ = ["ModelListParams"]


class ModelListParams(TypedDict, total=False):
    return_wildcard_routes: Optional[bool]

    team_id: Optional[str]
