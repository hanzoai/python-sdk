# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from __future__ import annotations

from typing import Optional
from typing_extensions import Required, TypedDict

from .._types import FileTypes

__all__ = ["FileCreateParams"]


class FileCreateParams(TypedDict, total=False):
    file: Required[FileTypes]

    purpose: Required[str]

    custom_llm_provider: str

    litellm_metadata: Optional[str]

    target_model_names: str

    target_storage: str
