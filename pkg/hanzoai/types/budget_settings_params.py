# Hanzo AI SDK

from __future__ import annotations

from typing_extensions import Required, TypedDict

__all__ = ["BudgetSettingsParams"]


class BudgetSettingsParams(TypedDict, total=False):
    budget_id: Required[str]
