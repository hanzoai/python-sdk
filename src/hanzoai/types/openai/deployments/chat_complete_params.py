# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from __future__ import annotations

from typing import Dict, Union, Iterable, Optional
from typing_extensions import Literal, Required, Annotated, TypeAlias, TypedDict

from ...._types import SequenceNotStr
from ...._utils import PropertyInfo

__all__ = [
    "ChatCompleteParams",
    "Message",
    "MessageChatCompletionUserMessage",
    "MessageChatCompletionUserMessageContentUnionMember1",
    "MessageChatCompletionUserMessageContentUnionMember1ChatCompletionTextObject",
    "MessageChatCompletionUserMessageContentUnionMember1ChatCompletionTextObjectCacheControl",
    "MessageChatCompletionUserMessageContentUnionMember1ChatCompletionImageObject",
    "MessageChatCompletionUserMessageContentUnionMember1ChatCompletionImageObjectImageURL",
    "MessageChatCompletionUserMessageContentUnionMember1ChatCompletionImageObjectImageURLChatCompletionImageURLObject",
    "MessageChatCompletionUserMessageContentUnionMember1ChatCompletionAudioObject",
    "MessageChatCompletionUserMessageContentUnionMember1ChatCompletionAudioObjectInputAudio",
    "MessageChatCompletionUserMessageContentUnionMember1ChatCompletionDocumentObject",
    "MessageChatCompletionUserMessageContentUnionMember1ChatCompletionDocumentObjectCitations",
    "MessageChatCompletionUserMessageContentUnionMember1ChatCompletionDocumentObjectSource",
    "MessageChatCompletionUserMessageContentUnionMember1ChatCompletionVideoObject",
    "MessageChatCompletionUserMessageContentUnionMember1ChatCompletionVideoObjectVideoURL",
    "MessageChatCompletionUserMessageContentUnionMember1ChatCompletionVideoObjectVideoURLChatCompletionVideoURLObject",
    "MessageChatCompletionUserMessageContentUnionMember1ChatCompletionFileObject",
    "MessageChatCompletionUserMessageContentUnionMember1ChatCompletionFileObjectFile",
    "MessageChatCompletionUserMessageCacheControl",
    "MessageChatCompletionAssistantMessage",
    "MessageChatCompletionAssistantMessageCacheControl",
    "MessageChatCompletionAssistantMessageContentUnionMember1",
    "MessageChatCompletionAssistantMessageContentUnionMember1ChatCompletionTextObject",
    "MessageChatCompletionAssistantMessageContentUnionMember1ChatCompletionTextObjectCacheControl",
    "MessageChatCompletionAssistantMessageContentUnionMember1ChatCompletionThinkingBlock",
    "MessageChatCompletionAssistantMessageContentUnionMember1ChatCompletionThinkingBlockCacheControl",
    "MessageChatCompletionAssistantMessageContentUnionMember1ChatCompletionThinkingBlockCacheControlChatCompletionCachedContent",
    "MessageChatCompletionAssistantMessageFunctionCall",
    "MessageChatCompletionAssistantMessageThinkingBlock",
    "MessageChatCompletionAssistantMessageThinkingBlockChatCompletionThinkingBlock",
    "MessageChatCompletionAssistantMessageThinkingBlockChatCompletionThinkingBlockCacheControl",
    "MessageChatCompletionAssistantMessageThinkingBlockChatCompletionThinkingBlockCacheControlChatCompletionCachedContent",
    "MessageChatCompletionAssistantMessageThinkingBlockChatCompletionRedactedThinkingBlock",
    "MessageChatCompletionAssistantMessageThinkingBlockChatCompletionRedactedThinkingBlockCacheControl",
    "MessageChatCompletionAssistantMessageThinkingBlockChatCompletionRedactedThinkingBlockCacheControlChatCompletionCachedContent",
    "MessageChatCompletionAssistantMessageToolCall",
    "MessageChatCompletionAssistantMessageToolCallFunction",
    "MessageChatCompletionToolMessage",
    "MessageChatCompletionToolMessageContentUnionMember1",
    "MessageChatCompletionToolMessageContentUnionMember1CacheControl",
    "MessageChatCompletionSystemMessage",
    "MessageChatCompletionSystemMessageCacheControl",
    "MessageChatCompletionFunctionMessage",
    "MessageChatCompletionFunctionMessageContentUnionMember1",
    "MessageChatCompletionFunctionMessageContentUnionMember1CacheControl",
    "MessageChatCompletionDeveloperMessage",
    "MessageChatCompletionDeveloperMessageCacheControl",
]


class ChatCompleteParams(TypedDict, total=False):
    messages: Required[Iterable[Message]]

    body_model: Required[Annotated[str, PropertyInfo(alias="model")]]

    caching: Optional[bool]

    context_window_fallback_dict: Optional[Dict[str, str]]

    fallbacks: Optional[SequenceNotStr[str]]

    frequency_penalty: Optional[float]

    function_call: Union[str, Dict[str, object], None]

    functions: Optional[Iterable[Dict[str, object]]]

    guardrails: Optional[SequenceNotStr[str]]

    logit_bias: Optional[Dict[str, float]]

    logprobs: Optional[bool]

    max_tokens: Optional[int]

    metadata: Optional[Dict[str, object]]

    n: Optional[int]

    num_retries: Optional[int]

    parallel_tool_calls: Optional[bool]

    presence_penalty: Optional[float]

    response_format: Optional[Dict[str, object]]

    seed: Optional[int]

    service_tier: Optional[str]

    stop: Union[str, SequenceNotStr[str], None]

    stream: Optional[bool]

    stream_options: Optional[Dict[str, object]]

    temperature: Optional[float]

    tool_choice: Union[str, Dict[str, object], None]

    tools: Optional[Iterable[Dict[str, object]]]

    top_logprobs: Optional[int]

    top_p: Optional[float]

    user: Optional[str]


class MessageChatCompletionUserMessageContentUnionMember1ChatCompletionTextObjectCacheControl(TypedDict, total=False):
    type: Required[Literal["ephemeral"]]


class MessageChatCompletionUserMessageContentUnionMember1ChatCompletionTextObject(TypedDict, total=False):
    text: Required[str]

    type: Required[Literal["text"]]

    cache_control: MessageChatCompletionUserMessageContentUnionMember1ChatCompletionTextObjectCacheControl


class MessageChatCompletionUserMessageContentUnionMember1ChatCompletionImageObjectImageURLChatCompletionImageURLObject(
    TypedDict, total=False
):
    url: Required[str]

    detail: str

    format: str


MessageChatCompletionUserMessageContentUnionMember1ChatCompletionImageObjectImageURL: TypeAlias = Union[
    str,
    MessageChatCompletionUserMessageContentUnionMember1ChatCompletionImageObjectImageURLChatCompletionImageURLObject,
]


class MessageChatCompletionUserMessageContentUnionMember1ChatCompletionImageObject(TypedDict, total=False):
    image_url: Required[MessageChatCompletionUserMessageContentUnionMember1ChatCompletionImageObjectImageURL]

    type: Required[Literal["image_url"]]


class MessageChatCompletionUserMessageContentUnionMember1ChatCompletionAudioObjectInputAudio(TypedDict, total=False):
    data: Required[str]

    format: Required[Literal["wav", "mp3"]]


class MessageChatCompletionUserMessageContentUnionMember1ChatCompletionAudioObject(TypedDict, total=False):
    input_audio: Required[MessageChatCompletionUserMessageContentUnionMember1ChatCompletionAudioObjectInputAudio]

    type: Required[Literal["input_audio"]]


class MessageChatCompletionUserMessageContentUnionMember1ChatCompletionDocumentObjectCitations(TypedDict, total=False):
    enabled: Required[bool]


class MessageChatCompletionUserMessageContentUnionMember1ChatCompletionDocumentObjectSource(TypedDict, total=False):
    data: Required[str]

    media_type: Required[str]

    type: Required[Literal["text"]]


class MessageChatCompletionUserMessageContentUnionMember1ChatCompletionDocumentObject(TypedDict, total=False):
    citations: Required[
        Optional[MessageChatCompletionUserMessageContentUnionMember1ChatCompletionDocumentObjectCitations]
    ]

    context: Required[str]

    source: Required[MessageChatCompletionUserMessageContentUnionMember1ChatCompletionDocumentObjectSource]

    title: Required[str]

    type: Required[Literal["document"]]


class MessageChatCompletionUserMessageContentUnionMember1ChatCompletionVideoObjectVideoURLChatCompletionVideoURLObject(
    TypedDict, total=False
):
    url: Required[str]

    detail: str


MessageChatCompletionUserMessageContentUnionMember1ChatCompletionVideoObjectVideoURL: TypeAlias = Union[
    str,
    MessageChatCompletionUserMessageContentUnionMember1ChatCompletionVideoObjectVideoURLChatCompletionVideoURLObject,
]


class MessageChatCompletionUserMessageContentUnionMember1ChatCompletionVideoObject(TypedDict, total=False):
    type: Required[Literal["video_url"]]

    video_url: Required[MessageChatCompletionUserMessageContentUnionMember1ChatCompletionVideoObjectVideoURL]


class MessageChatCompletionUserMessageContentUnionMember1ChatCompletionFileObjectFile(TypedDict, total=False):
    file_data: str

    file_id: str

    filename: str

    format: str


class MessageChatCompletionUserMessageContentUnionMember1ChatCompletionFileObject(TypedDict, total=False):
    file: Required[MessageChatCompletionUserMessageContentUnionMember1ChatCompletionFileObjectFile]

    type: Required[Literal["file"]]


MessageChatCompletionUserMessageContentUnionMember1: TypeAlias = Union[
    MessageChatCompletionUserMessageContentUnionMember1ChatCompletionTextObject,
    MessageChatCompletionUserMessageContentUnionMember1ChatCompletionImageObject,
    MessageChatCompletionUserMessageContentUnionMember1ChatCompletionAudioObject,
    MessageChatCompletionUserMessageContentUnionMember1ChatCompletionDocumentObject,
    MessageChatCompletionUserMessageContentUnionMember1ChatCompletionVideoObject,
    MessageChatCompletionUserMessageContentUnionMember1ChatCompletionFileObject,
]


class MessageChatCompletionUserMessageCacheControl(TypedDict, total=False):
    type: Required[Literal["ephemeral"]]


class MessageChatCompletionUserMessage(TypedDict, total=False):
    content: Required[Union[str, Iterable[MessageChatCompletionUserMessageContentUnionMember1]]]

    role: Required[Literal["user"]]

    cache_control: MessageChatCompletionUserMessageCacheControl


class MessageChatCompletionAssistantMessageCacheControl(TypedDict, total=False):
    type: Required[Literal["ephemeral"]]


class MessageChatCompletionAssistantMessageContentUnionMember1ChatCompletionTextObjectCacheControl(
    TypedDict, total=False
):
    type: Required[Literal["ephemeral"]]


class MessageChatCompletionAssistantMessageContentUnionMember1ChatCompletionTextObject(TypedDict, total=False):
    text: Required[str]

    type: Required[Literal["text"]]

    cache_control: MessageChatCompletionAssistantMessageContentUnionMember1ChatCompletionTextObjectCacheControl


class MessageChatCompletionAssistantMessageContentUnionMember1ChatCompletionThinkingBlockCacheControlChatCompletionCachedContent(
    TypedDict, total=False
):
    type: Required[Literal["ephemeral"]]


MessageChatCompletionAssistantMessageContentUnionMember1ChatCompletionThinkingBlockCacheControl: TypeAlias = Union[
    Dict[str, object],
    MessageChatCompletionAssistantMessageContentUnionMember1ChatCompletionThinkingBlockCacheControlChatCompletionCachedContent,
]


class MessageChatCompletionAssistantMessageContentUnionMember1ChatCompletionThinkingBlock(TypedDict, total=False):
    type: Required[Literal["thinking"]]

    cache_control: Optional[
        MessageChatCompletionAssistantMessageContentUnionMember1ChatCompletionThinkingBlockCacheControl
    ]

    signature: str

    thinking: str


MessageChatCompletionAssistantMessageContentUnionMember1: TypeAlias = Union[
    MessageChatCompletionAssistantMessageContentUnionMember1ChatCompletionTextObject,
    MessageChatCompletionAssistantMessageContentUnionMember1ChatCompletionThinkingBlock,
]


class MessageChatCompletionAssistantMessageFunctionCall(TypedDict, total=False):
    arguments: str

    name: Optional[str]

    provider_specific_fields: Optional[Dict[str, object]]


class MessageChatCompletionAssistantMessageThinkingBlockChatCompletionThinkingBlockCacheControlChatCompletionCachedContent(
    TypedDict, total=False
):
    type: Required[Literal["ephemeral"]]


MessageChatCompletionAssistantMessageThinkingBlockChatCompletionThinkingBlockCacheControl: TypeAlias = Union[
    Dict[str, object],
    MessageChatCompletionAssistantMessageThinkingBlockChatCompletionThinkingBlockCacheControlChatCompletionCachedContent,
]


class MessageChatCompletionAssistantMessageThinkingBlockChatCompletionThinkingBlock(TypedDict, total=False):
    type: Required[Literal["thinking"]]

    cache_control: Optional[MessageChatCompletionAssistantMessageThinkingBlockChatCompletionThinkingBlockCacheControl]

    signature: str

    thinking: str


class MessageChatCompletionAssistantMessageThinkingBlockChatCompletionRedactedThinkingBlockCacheControlChatCompletionCachedContent(
    TypedDict, total=False
):
    type: Required[Literal["ephemeral"]]


MessageChatCompletionAssistantMessageThinkingBlockChatCompletionRedactedThinkingBlockCacheControl: TypeAlias = Union[
    Dict[str, object],
    MessageChatCompletionAssistantMessageThinkingBlockChatCompletionRedactedThinkingBlockCacheControlChatCompletionCachedContent,
]


class MessageChatCompletionAssistantMessageThinkingBlockChatCompletionRedactedThinkingBlock(TypedDict, total=False):
    type: Required[Literal["redacted_thinking"]]

    cache_control: Optional[
        MessageChatCompletionAssistantMessageThinkingBlockChatCompletionRedactedThinkingBlockCacheControl
    ]

    data: str


MessageChatCompletionAssistantMessageThinkingBlock: TypeAlias = Union[
    MessageChatCompletionAssistantMessageThinkingBlockChatCompletionThinkingBlock,
    MessageChatCompletionAssistantMessageThinkingBlockChatCompletionRedactedThinkingBlock,
]


class MessageChatCompletionAssistantMessageToolCallFunction(TypedDict, total=False):
    arguments: str

    name: Optional[str]

    provider_specific_fields: Optional[Dict[str, object]]


class MessageChatCompletionAssistantMessageToolCall(TypedDict, total=False):
    id: Required[Optional[str]]

    function: Required[MessageChatCompletionAssistantMessageToolCallFunction]

    type: Required[Literal["function"]]


class MessageChatCompletionAssistantMessage(TypedDict, total=False):
    role: Required[Literal["assistant"]]

    cache_control: MessageChatCompletionAssistantMessageCacheControl

    content: Union[str, Iterable[MessageChatCompletionAssistantMessageContentUnionMember1], None]

    function_call: Optional[MessageChatCompletionAssistantMessageFunctionCall]

    name: Optional[str]

    reasoning_content: Optional[str]

    thinking_blocks: Optional[Iterable[MessageChatCompletionAssistantMessageThinkingBlock]]

    tool_calls: Optional[Iterable[MessageChatCompletionAssistantMessageToolCall]]


class MessageChatCompletionToolMessageContentUnionMember1CacheControl(TypedDict, total=False):
    type: Required[Literal["ephemeral"]]


class MessageChatCompletionToolMessageContentUnionMember1(TypedDict, total=False):
    text: Required[str]

    type: Required[Literal["text"]]

    cache_control: MessageChatCompletionToolMessageContentUnionMember1CacheControl


class MessageChatCompletionToolMessage(TypedDict, total=False):
    content: Required[Union[str, Iterable[MessageChatCompletionToolMessageContentUnionMember1]]]

    role: Required[Literal["tool"]]

    tool_call_id: Required[str]


class MessageChatCompletionSystemMessageCacheControl(TypedDict, total=False):
    type: Required[Literal["ephemeral"]]


class MessageChatCompletionSystemMessage(TypedDict, total=False):
    content: Required[Union[str, Iterable[object]]]

    role: Required[Literal["system"]]

    cache_control: MessageChatCompletionSystemMessageCacheControl

    name: str


class MessageChatCompletionFunctionMessageContentUnionMember1CacheControl(TypedDict, total=False):
    type: Required[Literal["ephemeral"]]


class MessageChatCompletionFunctionMessageContentUnionMember1(TypedDict, total=False):
    text: Required[str]

    type: Required[Literal["text"]]

    cache_control: MessageChatCompletionFunctionMessageContentUnionMember1CacheControl


class MessageChatCompletionFunctionMessage(TypedDict, total=False):
    content: Required[Union[str, Iterable[MessageChatCompletionFunctionMessageContentUnionMember1], None]]

    name: Required[str]

    role: Required[Literal["function"]]

    tool_call_id: Required[Optional[str]]


class MessageChatCompletionDeveloperMessageCacheControl(TypedDict, total=False):
    type: Required[Literal["ephemeral"]]


class MessageChatCompletionDeveloperMessage(TypedDict, total=False):
    content: Required[Union[str, Iterable[object]]]

    role: Required[Literal["developer"]]

    cache_control: MessageChatCompletionDeveloperMessageCacheControl

    name: str


Message: TypeAlias = Union[
    MessageChatCompletionUserMessage,
    MessageChatCompletionAssistantMessage,
    MessageChatCompletionToolMessage,
    MessageChatCompletionSystemMessage,
    MessageChatCompletionFunctionMessage,
    MessageChatCompletionDeveloperMessage,
]
