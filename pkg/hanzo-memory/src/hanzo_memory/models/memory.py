"""Memory models."""

from typing import Any, Optional, Union

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

    additional_context: Optional[str] = Field(
        None, description="Additional context for the memory"
    )
    strip_pii: bool = Field(False, description="Strip PII from content")


class MemoryUpdate(BaseModel):
    """Model for updating a memory."""

    content: Optional[str] = None
    metadata: Optional[dict[str, Any]] = None
    importance: Optional[float] = None


class Memory(MemoryBase, ProjectScopedModel, TimestampedModel):
    """Complete memory model."""

    memory_id: str = Field(..., description="Memory ID")
    embedding: Optional[list[float]] = Field(None, description="Embedding vector")

    model_config = {"from_attributes": True}


class MemoryWithScore(Memory):
    """Memory with similarity score."""

    similarity_score: float = Field(..., description="Similarity score")


class MemoryResponse(BaseModel):
    """Memory response model."""

    user_id: str = Field(..., description="User ID")
    relevant_memories: list[Union[str, dict[str, str]]] = Field(
        ..., description="Relevant memories"
    )
    memory_stored: bool = Field(True, description="Whether the memory was stored")
    usage_info: dict[str, int] = Field(..., description="Usage information")


class MemoryListResponse(BaseModel):
    """Memory list response."""

    user_id: str = Field(..., description="User ID")
    memories: list[Memory] = Field(..., description="List of memories")
    pagination: dict[str, Any] = Field(..., description="Pagination info")
    usage_info: dict[str, int] = Field(..., description="Usage information")


class RememberRequest(BaseModel):
    """Request model for /v1/remember endpoint."""

    apikey: Optional[str] = Field(None, description="API key")
    userid: str = Field(..., description="User ID")
    messagecontent: str = Field(..., description="Message content")
    additionalcontext: Optional[str] = Field(None, description="Additional context")
    strippii: bool = Field(False, description="Strip PII")
    filterresults: bool = Field(False, description="Filter results with LLM")
    includememoryid: bool = Field(False, description="Include memory IDs in response")


class AddMemoriesRequest(BaseModel):
    """Request model for /v1/memories/add endpoint."""

    apikey: Optional[str] = Field(None, description="API key")
    userid: str = Field(..., description="User ID")
    memoriestoadd: Union[str, list[str]] = Field(..., description="Memories to add")


class GetMemoriesRequest(BaseModel):
    """Request model for /v1/memories/get endpoint."""

    apikey: Optional[str] = Field(None, description="API key")
    userid: str = Field(..., description="User ID")
    memoryid: Optional[str] = Field(None, description="Specific memory ID")
    limit: int = Field(50, ge=1, le=1000, description="Max memories to return")
    startafter: Optional[str] = Field(None, description="Memory ID to start after")


class DeleteMemoryRequest(BaseModel):
    """Request model for /v1/memories/delete endpoint."""

    apikey: Optional[str] = Field(None, description="API key")
    userid: str = Field(..., description="User ID")
    memoryid: str = Field(..., description="Memory ID to delete")


class DeleteUserRequest(BaseModel):
    """Request model for /v1/user/delete endpoint."""

    apikey: Optional[str] = Field(None, description="API key")
    userid: str = Field(..., description="User ID")
    confirmdelete: bool = Field(..., description="Confirm deletion")
