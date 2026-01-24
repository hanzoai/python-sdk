# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from __future__ import annotations

from typing import Optional
from typing_extensions import Literal, TypedDict

__all__ = ["JobListParams"]


class JobListParams(TypedDict, total=False):
    after: Optional[str]

    custom_llm_provider: Optional[Literal["openai", "azure"]]

    limit: Optional[int]

    target_model_names: Optional[str]
    """Comma separated list of model names to filter by. Example: 'gpt-4o,gpt-4o-mini'"""
