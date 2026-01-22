# Hanzo AI SDK

from __future__ import annotations

from typing import Optional
from typing_extensions import TypedDict

__all__ = ["InfoListParams"]


class InfoListParams(TypedDict, total=False):
    hanzo_model_id: Optional[str]
