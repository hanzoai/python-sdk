# Hanzo AI SDK

from __future__ import annotations

from typing import List
from typing_extensions import Required, TypedDict

__all__ = ["CustomerDeleteParams"]


class CustomerDeleteParams(TypedDict, total=False):
    user_ids: Required[List[str]]
