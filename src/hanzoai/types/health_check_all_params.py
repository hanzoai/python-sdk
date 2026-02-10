# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from __future__ import annotations

from typing import Optional
from typing_extensions import TypedDict

__all__ = ["HealthCheckAllParams"]


class HealthCheckAllParams(TypedDict, total=False):
    model: Optional[str]
    """Specify the model name (optional)"""
