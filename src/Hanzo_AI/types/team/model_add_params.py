# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from __future__ import annotations

from typing import List
from typing_extensions import Required, TypedDict

__all__ = ["ModelAddParams"]


class ModelAddParams(TypedDict, total=False):
    models: Required[List[str]]

    team_id: Required[str]
