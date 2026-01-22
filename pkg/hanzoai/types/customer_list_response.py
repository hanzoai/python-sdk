# Hanzo AI SDK

from typing import List
from typing_extensions import TypeAlias

from .lite_llm_end_user_table import HanzoEndUserTable

__all__ = ["CustomerListResponse"]

CustomerListResponse: TypeAlias = List[HanzoEndUserTable]
