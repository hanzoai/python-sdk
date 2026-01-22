# Hanzo AI SDK

from __future__ import annotations

from typing_extensions import Required, TypedDict

__all__ = ["UtilGetSupportedOpenAIParamsParams"]


class UtilGetSupportedOpenAIParamsParams(TypedDict, total=False):
    model: Required[str]
