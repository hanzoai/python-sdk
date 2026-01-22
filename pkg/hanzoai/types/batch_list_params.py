# Hanzo AI SDK

from __future__ import annotations

from typing import Optional
from typing_extensions import TypedDict

__all__ = ["BatchListParams"]


class BatchListParams(TypedDict, total=False):
    after: Optional[str]

    limit: Optional[int]

    provider: Optional[str]
