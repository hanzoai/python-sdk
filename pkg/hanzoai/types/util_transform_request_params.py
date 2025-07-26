# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from __future__ import annotations

from typing_extensions import Literal, Required, TypedDict

__all__ = ["UtilTransformRequestParams"]


class UtilTransformRequestParams(TypedDict, total=False):
    call_type: Required[
        Literal[
            "embedding",
            "aembedding",
            "completion",
            "acompletion",
            "atext_completion",
            "text_completion",
            "image_generation",
            "aimage_generation",
            "moderation",
            "amoderation",
            "atranscription",
            "transcription",
            "aspeech",
            "speech",
            "rerank",
            "arerank",
            "_arealtime",
            "create_batch",
            "acreate_batch",
            "aretrieve_batch",
            "retrieve_batch",
            "pass_through_endpoint",
            "anthropic_messages",
            "get_assistants",
            "aget_assistants",
            "create_assistants",
            "acreate_assistants",
            "delete_assistant",
            "adelete_assistant",
            "acreate_thread",
            "create_thread",
            "aget_thread",
            "get_thread",
            "a_add_message",
            "add_message",
            "aget_messages",
            "get_messages",
            "arun_thread",
            "run_thread",
            "arun_thread_stream",
            "run_thread_stream",
            "afile_retrieve",
            "file_retrieve",
            "afile_delete",
            "file_delete",
            "afile_list",
            "file_list",
            "acreate_file",
            "create_file",
            "afile_content",
            "file_content",
            "create_fine_tuning_job",
            "acreate_fine_tuning_job",
            "acancel_fine_tuning_job",
            "cancel_fine_tuning_job",
            "alist_fine_tuning_jobs",
            "list_fine_tuning_jobs",
            "aretrieve_fine_tuning_job",
            "retrieve_fine_tuning_job",
            "responses",
            "aresponses",
        ]
    ]

    request_body: Required[object]
