# Hanzo AI SDK

from __future__ import annotations

from typing import Optional
from typing_extensions import TypedDict

__all__ = ["EmbeddingCreateParams"]


class EmbeddingCreateParams(TypedDict, total=False):
    model: Optional[str]
