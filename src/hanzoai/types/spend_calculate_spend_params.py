# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from __future__ import annotations

from typing import Iterable, Optional
from typing_extensions import TypedDict

__all__ = ["SpendCalculateSpendParams"]


class SpendCalculateSpendParams(TypedDict, total=False):
    completion_response: Optional[object]

    messages: Optional[Iterable[object]]

    model: Optional[str]
