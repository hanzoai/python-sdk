# Hanzo AI SDK

from typing import List
from typing_extensions import TypeAlias

from .lite_llm_spend_logs import HanzoSpendLogs

__all__ = ["SpendListTagsResponse"]

SpendListTagsResponse: TypeAlias = List[HanzoSpendLogs]
