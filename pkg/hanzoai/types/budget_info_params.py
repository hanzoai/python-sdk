# Hanzo AI SDK

from __future__ import annotations

from typing import List
from typing_extensions import Required, TypedDict

__all__ = ["BudgetInfoParams"]


class BudgetInfoParams(TypedDict, total=False):
    budgets: Required[List[str]]
