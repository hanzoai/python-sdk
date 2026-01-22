# Hanzo AI SDK

from __future__ import annotations

from typing import Optional
from typing_extensions import TypedDict

__all__ = ["CompletionCreateParams"]


class CompletionCreateParams(TypedDict, total=False):
    model: Optional[str]
