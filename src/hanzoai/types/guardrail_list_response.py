# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from typing import TYPE_CHECKING, Dict, List, Optional
from datetime import datetime
from typing_extensions import Literal

from pydantic import Field as FieldInfo

from .._models import BaseModel

__all__ = ["GuardrailListResponse", "Guardrail", "GuardrailLitellmParams", "GuardrailLitellmParamsCategoryThresholds"]


class GuardrailLitellmParamsCategoryThresholds(BaseModel):
    """Threshold configuration for Lakera guardrail categories"""

    jailbreak: Optional[float] = None

    prompt_injection: Optional[float] = None

    if TYPE_CHECKING:
        # Some versions of Pydantic <2.8.0 have a bug and don’t allow assigning a
        # value to this field, so for compatibility we avoid doing it at runtime.
        __pydantic_extra__: Dict[str, object] = FieldInfo(init=False)  # pyright: ignore[reportIncompatibleVariableOverride]

        # Stub to indicate that arbitrary properties are accepted.
        # To access properties that are not valid identifiers you can use `getattr`, e.g.
        # `getattr(obj, '$type')`
        def __getattr__(self, attr: str) -> object: ...
    else:
        __pydantic_extra__: Dict[str, object]


class GuardrailLitellmParams(BaseModel):
    additional_provider_specific_params: Optional[Dict[str, object]] = None
    """Additional provider-specific parameters for generic guardrail APIs"""

    api_base: Optional[str] = None
    """Base URL for the guardrail service API"""

    api_endpoint: Optional[str] = None
    """Optional custom API endpoint for Model Armor"""

    api_key: Optional[str] = None
    """API key for the guardrail service"""

    category_thresholds: Optional[GuardrailLitellmParamsCategoryThresholds] = None
    """Threshold configuration for Lakera guardrail categories"""

    credentials: Optional[str] = None
    """Path to Google Cloud credentials JSON file or JSON string"""

    default_on: Optional[bool] = None
    """Whether the guardrail is enabled by default"""

    detect_secrets_config: Optional[Dict[str, object]] = None
    """Configuration for detect-secrets guardrail"""

    experimental_use_latest_role_message_only: Optional[bool] = None
    """
    When True, guardrails only receive the latest message for the relevant role
    (e.g., newest user input pre-call, newest assistant output post-call)
    """

    fail_on_error: Optional[bool] = None
    """Whether to fail the request if Model Armor encounters an error"""

    guard_name: Optional[str] = None
    """Name of the guardrail in guardrails.ai"""

    location: Optional[str] = None
    """Google Cloud location/region (e.g., us-central1)"""

    mask_request_content: Optional[bool] = None
    """Will mask request content if guardrail makes any changes"""

    mask_response_content: Optional[bool] = None
    """Will mask response content if guardrail makes any changes"""

    model: Optional[str] = None
    """Optional field if guardrail requires a 'model' parameter"""

    pangea_input_recipe: Optional[str] = None
    """Recipe for input (LLM request)"""

    pangea_output_recipe: Optional[str] = None
    """Recipe for output (LLM response)"""

    template_id: Optional[str] = None
    """The ID of your Model Armor template"""

    violation_message_template: Optional[str] = None
    """Custom message when a guardrail blocks an action.

    Supports placeholders like {tool_name}, {rule_id}, and {default_message}.
    """

    if TYPE_CHECKING:
        # Some versions of Pydantic <2.8.0 have a bug and don’t allow assigning a
        # value to this field, so for compatibility we avoid doing it at runtime.
        __pydantic_extra__: Dict[str, object] = FieldInfo(init=False)  # pyright: ignore[reportIncompatibleVariableOverride]

        # Stub to indicate that arbitrary properties are accepted.
        # To access properties that are not valid identifiers you can use `getattr`, e.g.
        # `getattr(obj, '$type')`
        def __getattr__(self, attr: str) -> object: ...
    else:
        __pydantic_extra__: Dict[str, object]


class Guardrail(BaseModel):
    guardrail_name: str

    created_at: Optional[datetime] = None

    guardrail_definition_location: Optional[Literal["db", "config"]] = None

    guardrail_id: Optional[str] = None

    guardrail_info: Optional[Dict[str, object]] = None

    litellm_params: Optional[GuardrailLitellmParams] = None

    updated_at: Optional[datetime] = None


class GuardrailListResponse(BaseModel):
    guardrails: List[Guardrail]
