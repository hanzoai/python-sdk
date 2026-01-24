# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from __future__ import annotations

from typing import Optional
from typing_extensions import Literal, TypedDict

__all__ = ["JobRetrieveParams"]


class JobRetrieveParams(TypedDict, total=False):
    custom_llm_provider: Optional[Literal["openai", "azure"]]
