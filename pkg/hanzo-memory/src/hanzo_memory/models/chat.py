"""Chat models."""

from typing import Any, Optional

from pydantic import BaseModel, Field

from .base import ProjectScopedModel


class ChatMessageBase(BaseModel):
    """Base chat message model."""

    role: str = Field(..., description="Message role (user, assistant, system)")
    content: str = Field(..., description="Message content")
    metadata: dict[str, Any] = Field(
        default_factory=dict, description="Additional metadata"
    )


class ChatMessageCreate(ChatMessageBase):
    """Model for creating a chat message."""

    userid: str = Field(..., description="User ID")
    session_id: str = Field(..., description="Chat session ID")
    project_id: Optional[str] = Field(None, description="Project ID")


class ChatMessage(ChatMessageBase, ProjectScopedModel):
    """Complete chat message model."""

    chat_id: str = Field(..., description="Chat message ID")
    session_id: str = Field(..., description="Chat session ID")
    embedding: Optional[list[float]] = Field(None, description="Message embedding")
    created_at: str = Field(..., description="Creation timestamp")

    model_config = {"from_attributes": True}


class ChatSessionCreate(BaseModel):
    """Model for creating a chat session."""

    userid: str = Field(..., description="User ID")
    session_id: Optional[str] = Field(None, description="Custom session ID")
    project_id: Optional[str] = Field(None, description="Project ID")
    title: Optional[str] = Field(None, description="Session title")
    metadata: dict[str, Any] = Field(
        default_factory=dict, description="Session metadata"
    )


class ChatSession(BaseModel):
    """Chat session model."""

    session_id: str = Field(..., description="Session ID")
    user_id: str = Field(..., description="User ID")
    project_id: str = Field(..., description="Project ID")
    title: Optional[str] = Field(None, description="Session title")
    metadata: dict[str, Any] = Field(
        default_factory=dict, description="Session metadata"
    )
    created_at: str = Field(..., description="Creation timestamp")
    updated_at: str = Field(..., description="Last update timestamp")
    message_count: int = Field(0, description="Number of messages in session")


class ChatHistoryRequest(BaseModel):
    """Request model for chat history."""

    user_id: str = Field(..., description="User ID")
    session_id: str = Field(..., description="Session ID")
    limit: int = Field(100, ge=1, le=1000, description="Max messages to return")
    offset: int = Field(0, ge=0, description="Offset for pagination")


class ChatSearchRequest(BaseModel):
    """Request model for chat search."""

    user_id: str = Field(..., description="User ID")
    query: str = Field(..., description="Search query")
    project_id: Optional[str] = Field(None, description="Filter by project ID")
    session_id: Optional[str] = Field(None, description="Filter by session ID")
    limit: int = Field(10, ge=1, le=100, description="Max results to return")


class ChatSessionList(BaseModel):
    """Chat session list response."""

    sessions: list[ChatSession] = Field(..., description="List of chat sessions")
    total: int = Field(..., description="Total number of sessions")
    page: int = Field(1, description="Current page")
    per_page: int = Field(50, description="Items per page")
