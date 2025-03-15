# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from __future__ import annotations

from typing import Optional
from typing_extensions import Literal, Required, TypedDict

__all__ = ["CustomerUpdateParams"]


class CustomerUpdateParams(TypedDict, total=False):
    user_id: Required[str]

    alias: Optional[str]

    allowed_model_region: Optional[Literal["eu", "us"]]

    blocked: bool

    budget_id: Optional[str]

    default_model: Optional[str]

    max_budget: Optional[float]
