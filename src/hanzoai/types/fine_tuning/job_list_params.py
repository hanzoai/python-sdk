# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from __future__ import annotations

from typing import Optional
from typing_extensions import Literal, Required, TypedDict

__all__ = ["JobListParams"]


class JobListParams(TypedDict, total=False):
    custom_llm_provider: Required[Literal["openai", "azure"]]

    after: Optional[str]

    limit: Optional[int]
