# Hanzo AI SDK

from __future__ import annotations

from typing import Optional
from typing_extensions import TypedDict

__all__ = ["BatchCreateParams"]


class BatchCreateParams(TypedDict, total=False):
    provider: Optional[str]
