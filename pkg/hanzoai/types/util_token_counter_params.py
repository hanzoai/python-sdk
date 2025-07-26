# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from __future__ import annotations

from typing import Iterable, Optional
from typing_extensions import Required, TypedDict

__all__ = ["UtilTokenCounterParams"]


class UtilTokenCounterParams(TypedDict, total=False):
    model: Required[str]

    messages: Optional[Iterable[object]]

    prompt: Optional[str]
