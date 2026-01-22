# Hanzo AI SDK

from __future__ import annotations

from typing_extensions import Literal, Required, TypedDict

__all__ = ["JobRetrieveParams"]


class JobRetrieveParams(TypedDict, total=False):
    custom_llm_provider: Required[Literal["openai", "azure"]]
