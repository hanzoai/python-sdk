# Hanzo AI SDK

from __future__ import annotations

from typing import List
from typing_extensions import Required, TypedDict

__all__ = ["CustomerBlockParams"]


class CustomerBlockParams(TypedDict, total=False):
    user_ids: Required[List[str]]
