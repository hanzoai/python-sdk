# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from typing import List, Union, Optional

from .._models import BaseModel

__all__ = ["GuardrailListResponse", "Guardrail", "GuardrailLlmParams"]


class GuardrailLlmParams(BaseModel):
    guardrail: str

    mode: Union[str, List[str]]

    default_on: Optional[bool] = None


class Guardrail(BaseModel):
    guardrail_info: Optional[object] = None

    guardrail_name: str

    llm_params: GuardrailLlmParams
    """The returned LLM Params object for /guardrails/list"""


class GuardrailListResponse(BaseModel):
    guardrails: List[Guardrail]
