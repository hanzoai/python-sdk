# Hanzo AI SDK

from __future__ import annotations

from typing import Optional
from typing_extensions import TypedDict

__all__ = ["CancelCancelParams"]


class CancelCancelParams(TypedDict, total=False):
    provider: Optional[str]
