# Hanzo AI SDK

from __future__ import annotations

from typing import Optional
from typing_extensions import TypedDict

__all__ = ["ModelGroupRetrieveInfoParams"]


class ModelGroupRetrieveInfoParams(TypedDict, total=False):
    model_group: Optional[str]
