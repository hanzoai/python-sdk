# Hanzo AI SDK

from __future__ import annotations

from typing_extensions import Required, TypedDict

__all__ = ["BudgetDeleteParams"]


class BudgetDeleteParams(TypedDict, total=False):
    id: Required[str]
