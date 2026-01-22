# Hanzo AI SDK

from __future__ import annotations

from typing import Optional
from typing_extensions import TypedDict

__all__ = ["KeyRetrieveInfoParams"]


class KeyRetrieveInfoParams(TypedDict, total=False):
    key: Optional[str]
    """Key in the request parameters"""
