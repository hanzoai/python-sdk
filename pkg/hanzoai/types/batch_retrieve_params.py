# Hanzo AI SDK

from __future__ import annotations

from typing import Optional
from typing_extensions import TypedDict

__all__ = ["BatchRetrieveParams"]


class BatchRetrieveParams(TypedDict, total=False):
    provider: Optional[str]
