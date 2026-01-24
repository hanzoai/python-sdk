# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from __future__ import annotations

import builtins
from typing import Dict, Union, Iterable, Optional
from typing_extensions import Literal, Required, TypeAlias, TypedDict

from .._types import SequenceNotStr
from .model_info_param import ModelInfoParam

__all__ = [
    "ModelCreateParams",
    "LitellmParams",
    "LitellmParamsConfigurableClientsideAuthParam",
    "LitellmParamsConfigurableClientsideAuthParamConfigurableClientsideParamsCustomAuthInput",
    "LitellmParamsMockResponse",
    "LitellmParamsMockResponseModelResponse",
    "LitellmParamsMockResponseModelResponseChoice",
    "LitellmParamsMockResponseModelResponseChoiceChoices",
    "LitellmParamsMockResponseModelResponseChoiceChoicesMessage",
    "LitellmParamsMockResponseModelResponseChoiceChoicesMessageFunctionCall",
    "LitellmParamsMockResponseModelResponseChoiceChoicesMessageAnnotation",
    "LitellmParamsMockResponseModelResponseChoiceChoicesMessageAnnotationURLCitation",
    "LitellmParamsMockResponseModelResponseChoiceChoicesMessageAudio",
    "LitellmParamsMockResponseModelResponseChoiceChoicesMessageImage",
    "LitellmParamsMockResponseModelResponseChoiceChoicesMessageImageImageURL",
    "LitellmParamsMockResponseModelResponseChoiceChoicesMessageThinkingBlock",
    "LitellmParamsMockResponseModelResponseChoiceChoicesMessageThinkingBlockChatCompletionThinkingBlock",
    "LitellmParamsMockResponseModelResponseChoiceChoicesMessageThinkingBlockChatCompletionThinkingBlockCacheControl",
    "LitellmParamsMockResponseModelResponseChoiceChoicesMessageThinkingBlockChatCompletionThinkingBlockCacheControlChatCompletionCachedContent",
    "LitellmParamsMockResponseModelResponseChoiceChoicesMessageThinkingBlockChatCompletionRedactedThinkingBlock",
    "LitellmParamsMockResponseModelResponseChoiceChoicesMessageThinkingBlockChatCompletionRedactedThinkingBlockCacheControl",
    "LitellmParamsMockResponseModelResponseChoiceChoicesMessageThinkingBlockChatCompletionRedactedThinkingBlockCacheControlChatCompletionCachedContent",
    "LitellmParamsMockResponseModelResponseChoiceChoicesLogprobs",
    "LitellmParamsMockResponseModelResponseChoiceChoicesLogprobsChoiceLogprobs",
    "LitellmParamsMockResponseModelResponseChoiceChoicesLogprobsChoiceLogprobsContent",
    "LitellmParamsMockResponseModelResponseChoiceChoicesLogprobsChoiceLogprobsContentTopLogprob",
]


class ModelCreateParams(TypedDict, total=False):
    litellm_params: Required[LitellmParams]
    """LiteLLM Params with 'model' requirement - used for completions"""

    model_info: Required[ModelInfoParam]

    model_name: Required[str]


class LitellmParamsConfigurableClientsideAuthParamConfigurableClientsideParamsCustomAuthInputTyped(
    TypedDict, total=False
):
    api_base: Required[str]


LitellmParamsConfigurableClientsideAuthParamConfigurableClientsideParamsCustomAuthInput: TypeAlias = Union[
    LitellmParamsConfigurableClientsideAuthParamConfigurableClientsideParamsCustomAuthInputTyped, Dict[str, object]
]

LitellmParamsConfigurableClientsideAuthParam: TypeAlias = Union[
    str, LitellmParamsConfigurableClientsideAuthParamConfigurableClientsideParamsCustomAuthInput
]


class LitellmParamsMockResponseModelResponseChoiceChoicesMessageFunctionCallTyped(TypedDict, total=False):
    arguments: Required[str]

    name: Optional[str]


LitellmParamsMockResponseModelResponseChoiceChoicesMessageFunctionCall: TypeAlias = Union[
    LitellmParamsMockResponseModelResponseChoiceChoicesMessageFunctionCallTyped, Dict[str, object]
]


class LitellmParamsMockResponseModelResponseChoiceChoicesMessageAnnotationURLCitationTyped(TypedDict, total=False):
    end_index: int

    start_index: int

    title: str

    url: str


LitellmParamsMockResponseModelResponseChoiceChoicesMessageAnnotationURLCitation: TypeAlias = Union[
    LitellmParamsMockResponseModelResponseChoiceChoicesMessageAnnotationURLCitationTyped, Dict[str, object]
]


class LitellmParamsMockResponseModelResponseChoiceChoicesMessageAnnotationTyped(TypedDict, total=False):
    type: Literal["url_citation"]

    url_citation: LitellmParamsMockResponseModelResponseChoiceChoicesMessageAnnotationURLCitation


LitellmParamsMockResponseModelResponseChoiceChoicesMessageAnnotation: TypeAlias = Union[
    LitellmParamsMockResponseModelResponseChoiceChoicesMessageAnnotationTyped, Dict[str, object]
]


class LitellmParamsMockResponseModelResponseChoiceChoicesMessageAudioTyped(TypedDict, total=False):
    id: Required[str]

    data: Required[str]

    expires_at: Required[int]

    transcript: Required[str]


LitellmParamsMockResponseModelResponseChoiceChoicesMessageAudio: TypeAlias = Union[
    LitellmParamsMockResponseModelResponseChoiceChoicesMessageAudioTyped, Dict[str, object]
]


class LitellmParamsMockResponseModelResponseChoiceChoicesMessageImageImageURLTyped(TypedDict, total=False):
    url: Required[str]

    detail: Optional[str]


LitellmParamsMockResponseModelResponseChoiceChoicesMessageImageImageURL: TypeAlias = Union[
    LitellmParamsMockResponseModelResponseChoiceChoicesMessageImageImageURLTyped, Dict[str, object]
]


class LitellmParamsMockResponseModelResponseChoiceChoicesMessageImageTyped(TypedDict, total=False):
    image_url: Required[LitellmParamsMockResponseModelResponseChoiceChoicesMessageImageImageURL]

    index: Required[int]

    type: Required[Literal["image_url"]]


LitellmParamsMockResponseModelResponseChoiceChoicesMessageImage: TypeAlias = Union[
    LitellmParamsMockResponseModelResponseChoiceChoicesMessageImageTyped, Dict[str, object]
]


class LitellmParamsMockResponseModelResponseChoiceChoicesMessageThinkingBlockChatCompletionThinkingBlockCacheControlChatCompletionCachedContent(
    TypedDict, total=False
):
    type: Required[Literal["ephemeral"]]


LitellmParamsMockResponseModelResponseChoiceChoicesMessageThinkingBlockChatCompletionThinkingBlockCacheControl: TypeAlias = Union[
    Dict[str, object],
    LitellmParamsMockResponseModelResponseChoiceChoicesMessageThinkingBlockChatCompletionThinkingBlockCacheControlChatCompletionCachedContent,
]


class LitellmParamsMockResponseModelResponseChoiceChoicesMessageThinkingBlockChatCompletionThinkingBlock(
    TypedDict, total=False
):
    type: Required[Literal["thinking"]]

    cache_control: Optional[
        LitellmParamsMockResponseModelResponseChoiceChoicesMessageThinkingBlockChatCompletionThinkingBlockCacheControl
    ]

    signature: str

    thinking: str


class LitellmParamsMockResponseModelResponseChoiceChoicesMessageThinkingBlockChatCompletionRedactedThinkingBlockCacheControlChatCompletionCachedContent(
    TypedDict, total=False
):
    type: Required[Literal["ephemeral"]]


LitellmParamsMockResponseModelResponseChoiceChoicesMessageThinkingBlockChatCompletionRedactedThinkingBlockCacheControl: TypeAlias = Union[
    Dict[str, object],
    LitellmParamsMockResponseModelResponseChoiceChoicesMessageThinkingBlockChatCompletionRedactedThinkingBlockCacheControlChatCompletionCachedContent,
]


class LitellmParamsMockResponseModelResponseChoiceChoicesMessageThinkingBlockChatCompletionRedactedThinkingBlock(
    TypedDict, total=False
):
    type: Required[Literal["redacted_thinking"]]

    cache_control: Optional[
        LitellmParamsMockResponseModelResponseChoiceChoicesMessageThinkingBlockChatCompletionRedactedThinkingBlockCacheControl
    ]

    data: str


LitellmParamsMockResponseModelResponseChoiceChoicesMessageThinkingBlock: TypeAlias = Union[
    LitellmParamsMockResponseModelResponseChoiceChoicesMessageThinkingBlockChatCompletionThinkingBlock,
    LitellmParamsMockResponseModelResponseChoiceChoicesMessageThinkingBlockChatCompletionRedactedThinkingBlock,
]


class LitellmParamsMockResponseModelResponseChoiceChoicesMessageTyped(TypedDict, total=False):
    content: Required[Optional[str]]

    function_call: Required[Optional[LitellmParamsMockResponseModelResponseChoiceChoicesMessageFunctionCall]]

    role: Required[Literal["assistant", "user", "system", "tool", "function"]]

    tool_calls: Required[Optional[Iterable[Dict[str, object]]]]

    annotations: Optional[Iterable[LitellmParamsMockResponseModelResponseChoiceChoicesMessageAnnotation]]

    audio: Optional[LitellmParamsMockResponseModelResponseChoiceChoicesMessageAudio]

    images: Optional[Iterable[LitellmParamsMockResponseModelResponseChoiceChoicesMessageImage]]

    provider_specific_fields: Optional[Dict[str, object]]

    reasoning_content: Optional[str]

    thinking_blocks: Optional[Iterable[LitellmParamsMockResponseModelResponseChoiceChoicesMessageThinkingBlock]]


LitellmParamsMockResponseModelResponseChoiceChoicesMessage: TypeAlias = Union[
    LitellmParamsMockResponseModelResponseChoiceChoicesMessageTyped, Dict[str, object]
]


class LitellmParamsMockResponseModelResponseChoiceChoicesLogprobsChoiceLogprobsContentTopLogprobTyped(
    TypedDict, total=False
):
    token: Required[str]

    logprob: Required[float]

    bytes: Optional[Iterable[int]]


LitellmParamsMockResponseModelResponseChoiceChoicesLogprobsChoiceLogprobsContentTopLogprob: TypeAlias = Union[
    LitellmParamsMockResponseModelResponseChoiceChoicesLogprobsChoiceLogprobsContentTopLogprobTyped, Dict[str, object]
]


class LitellmParamsMockResponseModelResponseChoiceChoicesLogprobsChoiceLogprobsContentTyped(TypedDict, total=False):
    token: Required[str]

    logprob: Required[float]

    top_logprobs: Required[
        Iterable[LitellmParamsMockResponseModelResponseChoiceChoicesLogprobsChoiceLogprobsContentTopLogprob]
    ]

    bytes: Optional[Iterable[int]]


LitellmParamsMockResponseModelResponseChoiceChoicesLogprobsChoiceLogprobsContent: TypeAlias = Union[
    LitellmParamsMockResponseModelResponseChoiceChoicesLogprobsChoiceLogprobsContentTyped, Dict[str, object]
]


class LitellmParamsMockResponseModelResponseChoiceChoicesLogprobsChoiceLogprobsTyped(TypedDict, total=False):
    content: Optional[Iterable[LitellmParamsMockResponseModelResponseChoiceChoicesLogprobsChoiceLogprobsContent]]


LitellmParamsMockResponseModelResponseChoiceChoicesLogprobsChoiceLogprobs: TypeAlias = Union[
    LitellmParamsMockResponseModelResponseChoiceChoicesLogprobsChoiceLogprobsTyped, Dict[str, object]
]

LitellmParamsMockResponseModelResponseChoiceChoicesLogprobs: TypeAlias = Union[
    LitellmParamsMockResponseModelResponseChoiceChoicesLogprobsChoiceLogprobs, object
]


class LitellmParamsMockResponseModelResponseChoiceChoicesTyped(TypedDict, total=False):
    finish_reason: Required[str]

    index: Required[int]

    message: Required[LitellmParamsMockResponseModelResponseChoiceChoicesMessage]

    logprobs: Optional[LitellmParamsMockResponseModelResponseChoiceChoicesLogprobs]

    provider_specific_fields: Optional[Dict[str, object]]


LitellmParamsMockResponseModelResponseChoiceChoices: TypeAlias = Union[
    LitellmParamsMockResponseModelResponseChoiceChoicesTyped, Dict[str, object]
]

LitellmParamsMockResponseModelResponseChoice: TypeAlias = Union[
    LitellmParamsMockResponseModelResponseChoiceChoices, Dict[str, object]
]


class LitellmParamsMockResponseModelResponseTyped(TypedDict, total=False):
    id: Required[str]

    choices: Required[Iterable[LitellmParamsMockResponseModelResponseChoice]]

    created: Required[int]

    object: Required[str]

    model: Optional[str]

    system_fingerprint: Optional[str]


LitellmParamsMockResponseModelResponse: TypeAlias = Union[
    LitellmParamsMockResponseModelResponseTyped, Dict[str, builtins.object]
]

LitellmParamsMockResponse: TypeAlias = Union[str, LitellmParamsMockResponseModelResponse, builtins.object]


class LitellmParamsTyped(TypedDict, total=False):
    """LiteLLM Params with 'model' requirement - used for completions"""

    model: Required[str]

    api_base: Optional[str]

    api_key: Optional[str]

    api_version: Optional[str]

    auto_router_config: Optional[str]

    auto_router_config_path: Optional[str]

    auto_router_default_model: Optional[str]

    auto_router_embedding_model: Optional[str]

    aws_access_key_id: Optional[str]

    aws_bedrock_runtime_endpoint: Optional[str]

    aws_region_name: Optional[str]

    aws_secret_access_key: Optional[str]

    budget_duration: Optional[str]

    cache_creation_input_audio_token_cost: Optional[float]

    cache_creation_input_token_cost: Optional[float]

    cache_creation_input_token_cost_above_1hr: Optional[float]

    cache_creation_input_token_cost_above_200k_tokens: Optional[float]

    cache_read_input_audio_token_cost: Optional[float]

    cache_read_input_token_cost: Optional[float]

    cache_read_input_token_cost_above_200k_tokens: Optional[float]

    cache_read_input_token_cost_flex: Optional[float]

    cache_read_input_token_cost_priority: Optional[float]

    citation_cost_per_token: Optional[float]

    configurable_clientside_auth_params: Optional[SequenceNotStr[LitellmParamsConfigurableClientsideAuthParam]]

    custom_llm_provider: Optional[str]

    gcs_bucket_name: Optional[str]

    input_cost_per_audio_per_second: Optional[float]

    input_cost_per_audio_per_second_above_128k_tokens: Optional[float]

    input_cost_per_audio_token: Optional[float]

    input_cost_per_character: Optional[float]

    input_cost_per_character_above_128k_tokens: Optional[float]

    input_cost_per_image: Optional[float]

    input_cost_per_image_above_128k_tokens: Optional[float]

    input_cost_per_pixel: Optional[float]

    input_cost_per_query: Optional[float]

    input_cost_per_second: Optional[float]

    input_cost_per_token: Optional[float]

    input_cost_per_token_above_128k_tokens: Optional[float]

    input_cost_per_token_above_200k_tokens: Optional[float]

    input_cost_per_token_batches: Optional[float]

    input_cost_per_token_cache_hit: Optional[float]

    input_cost_per_token_flex: Optional[float]

    input_cost_per_token_priority: Optional[float]

    input_cost_per_video_per_second: Optional[float]

    input_cost_per_video_per_second_above_128k_tokens: Optional[float]

    input_cost_per_video_per_second_above_15s_interval: Optional[float]

    input_cost_per_video_per_second_above_8s_interval: Optional[float]

    litellm_credential_name: Optional[str]

    litellm_trace_id: Optional[str]

    max_budget: Optional[float]

    max_file_size_mb: Optional[float]

    max_retries: Optional[int]

    merge_reasoning_content_in_choices: Optional[bool]

    milvus_text_field: Optional[str]

    mock_response: Optional[LitellmParamsMockResponse]

    model_info: Optional[Dict[str, object]]

    organization: Optional[str]

    output_cost_per_audio_per_second: Optional[float]

    output_cost_per_audio_token: Optional[float]

    output_cost_per_character: Optional[float]

    output_cost_per_character_above_128k_tokens: Optional[float]

    output_cost_per_image: Optional[float]

    output_cost_per_image_token: Optional[float]

    output_cost_per_pixel: Optional[float]

    output_cost_per_reasoning_token: Optional[float]

    output_cost_per_second: Optional[float]

    output_cost_per_token: Optional[float]

    output_cost_per_token_above_128k_tokens: Optional[float]

    output_cost_per_token_above_200k_tokens: Optional[float]

    output_cost_per_token_batches: Optional[float]

    output_cost_per_token_flex: Optional[float]

    output_cost_per_token_priority: Optional[float]

    output_cost_per_video_per_second: Optional[float]

    region_name: Optional[str]

    rpm: Optional[int]

    s3_bucket_name: Optional[str]

    s3_encryption_key_id: Optional[str]

    search_context_cost_per_query: Optional[Dict[str, object]]

    stream_timeout: Union[float, str, None]

    tiered_pricing: Optional[Iterable[Dict[str, object]]]

    timeout: Union[float, str, None]

    tpm: Optional[int]

    use_in_pass_through: Optional[bool]

    use_litellm_proxy: Optional[bool]

    vector_store_id: Optional[str]

    vertex_credentials: Union[str, Dict[str, object], None]

    vertex_location: Optional[str]

    vertex_project: Optional[str]

    watsonx_region_name: Optional[str]


LitellmParams: TypeAlias = Union[LitellmParamsTyped, Dict[str, object]]
