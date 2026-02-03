"""Memory models."""

from typing import Any

from pydantic import BaseModel, Field

from .base import ProjectScopedModel, TimestampedModel


class MemoryBase(BaseModel):
    """Base memory model."""

    content: str = Field(..., description="Memory content")
    metadata: dict[str, Any] = Field(
        default_factory=dict, description="Additional metadata"
    )
    importance: float = Field(1.0, ge=0.0, le=10.0, description="Importance score")


class MemoryCreate(MemoryBase):
    """Model for creating a memory."""

    additional_context: str | None = Field(
        None, description="Additional context for the memory"
    )
    strip_pii: bool = Field(False, description="Strip PII from content")
    memory_type: str | None = Field(None, description="Type of memory")
    context: dict[str, Any] | None = Field(None, description="Context information")
    source: str | None = Field(None, description="Source of the memory")
    embedding: list[float] | None = Field(None, description="Embedding vector")


class MemoryUpdate(BaseModel):
    """Model for updating a memory."""

    content: str | None = None
    metadata: dict[str, Any] | None = None
    importance: float | None = None


class Memory(MemoryBase, ProjectScopedModel, TimestampedModel):
    """Complete memory model."""

    memory_id: str | None = Field(None, description="Memory ID")
    id: str | None = Field(None, description="Memory ID alias")
    embedding: list[float] | None = Field(None, description="Embedding vector")
    memory_type: str | None = Field(None, description="Type of memory")
    context: dict[str, Any] | None = Field(None, description="Context information")
    source: str | None = Field(None, description="Source of the memory")
    timestamp: str | None = Field(None, description="Timestamp")

    model_config = {"from_attributes": True}


class MemoryWithScore(Memory):
    """Memory with similarity score."""

    similarity_score: float = Field(..., description="Similarity score")


class MemoryResponse(BaseModel):
    """Memory response model with search results."""

    memory: Memory | None = Field(None, description="Memory object")
    similarity: float | None = Field(None, description="Similarity score")
    relevance_score: float | None = Field(None, description="Relevance score")

    # Legacy fields for compatibility
    user_id: str | None = Field(None, description="User ID")
    relevant_memories: list[str | dict[str, str]] | None = Field(
        None, description="Relevant memories"
    )
    memory_stored: bool | None = Field(None, description="Whether the memory was stored")
    usage_info: dict[str, int] | None = Field(None, description="Usage information")


class MemoryListResponse(BaseModel):
    """Memory list response."""

    user_id: str = Field(..., description="User ID")
    memories: list[Memory] = Field(..., description="List of memories")
    pagination: dict[str, Any] = Field(..., description="Pagination info")
    usage_info: dict[str, int] = Field(..., description="Usage information")


class RememberRequest(BaseModel):
    """Request model for /v1/remember endpoint."""

    apikey: str | None = Field(None, description="API key")
    userid: str = Field(..., description="User ID")
    messagecontent: str = Field(..., description="Message content")
    additionalcontext: str | None = Field(None, description="Additional context")
    strippii: bool = Field(False, description="Strip PII")
    filterresults: bool = Field(False, description="Filter results with LLM")
    includememoryid: bool = Field(False, description="Include memory IDs in response")


class AddMemoriesRequest(BaseModel):
    """Request model for /v1/memories/add endpoint."""

    apikey: str | None = Field(None, description="API key")
    userid: str = Field(..., description="User ID")
    memoriestoadd: str | list[str] = Field(..., description="Memories to add")


class GetMemoriesRequest(BaseModel):
    """Request model for /v1/memories/get endpoint."""

    apikey: str | None = Field(None, description="API key")
    userid: str = Field(..., description="User ID")
    memoryid: str | None = Field(None, description="Specific memory ID")
    limit: int = Field(50, ge=1, le=1000, description="Max memories to return")
    startafter: str | None = Field(None, description="Memory ID to start after")


class DeleteMemoryRequest(BaseModel):
    """Request model for /v1/memories/delete endpoint."""

    apikey: str | None = Field(None, description="API key")
    userid: str = Field(..., description="User ID")
    memoryid: str = Field(..., description="Memory ID to delete")


class UpdateMemoryRequest(BaseModel):
    """Request model for /v1/memories/update endpoint."""

    apikey: str | None = Field(None, description="API key")
    userid: str = Field(..., description="User ID")
    memoryid: str = Field(..., description="Memory ID to update")
    projectid: str = Field(..., description="Project ID")
    content: str | None = Field(None, description="New content")
    importance: float | None = Field(None, ge=0.0, le=10.0, description="New importance score")
    metadata: dict[str, Any] | None = Field(None, description="New metadata")


class DeleteUserRequest(BaseModel):
    """Request model for /v1/user/delete endpoint."""

    apikey: str | None = Field(None, description="API key")
    userid: str = Field(..., description="User ID")
    confirmdelete: bool = Field(..., description="Confirm deletion")
