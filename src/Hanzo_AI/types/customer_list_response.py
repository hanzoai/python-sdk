# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from typing import List
from typing_extensions import TypeAlias

from .lite_llm_end_user_table import LiteLlmEndUserTable

__all__ = ["CustomerListResponse"]

CustomerListResponse: TypeAlias = List[LiteLlmEndUserTable]
