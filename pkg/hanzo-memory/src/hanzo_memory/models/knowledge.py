"""Knowledge base and fact models."""

from typing import Any

from pydantic import BaseModel, Field

from .base import ProjectScopedModel, TimestampedModel


class KnowledgeBaseBase(BaseModel):
    """Base knowledge base model."""

    name: str = Field(..., description="Knowledge base name")
    description: str = Field("", description="Knowledge base description")
    metadata: dict[str, Any] = Field(
        default_factory=dict, description="Additional metadata"
    )


class KnowledgeBaseCreate(KnowledgeBaseBase):
    """Model for creating a knowledge base."""

    kb_id: str | None = Field(None, description="Custom knowledge base ID")


class KnowledgeBaseUpdate(BaseModel):
    """Model for updating a knowledge base."""

    name: str | None = None
    description: str | None = None
    metadata: dict[str, Any] | None = None


class KnowledgeBase(KnowledgeBaseBase, ProjectScopedModel, TimestampedModel):
    """Complete knowledge base model."""

    kb_id: str = Field(..., description="Knowledge base ID")
    fact_count: int = Field(0, description="Number of facts in knowledge base")

    model_config = {"from_attributes": True}


class FactBase(BaseModel):
    """Base fact model."""

    content: str = Field(..., description="Fact content")
    metadata: dict[str, Any] = Field(
        default_factory=dict, description="Additional metadata"
    )
    parent_id: str | None = Field(None, description="Parent fact ID")


class FactCreate(FactBase):
    """Model for creating a fact."""

    fact_id: str | None = Field(None, description="Custom fact ID")


class FactUpdate(BaseModel):
    """Model for updating a fact."""

    content: str | None = None
    metadata: dict[str, Any] | None = None
    parent_id: str | None = None


class Fact(FactBase, TimestampedModel):
    """Complete fact model."""

    fact_id: str = Field(..., description="Fact ID")
    kb_id: str = Field(..., description="Knowledge base ID")
    embedding: list[float] | None = Field(None, description="Embedding vector")

    model_config = {"from_attributes": True}


class FactWithScore(Fact):
    """Fact with similarity score."""

    similarity_score: float = Field(..., description="Similarity score")


class FactRelation(BaseModel):
    """Fact relation model."""

    parent_fact_id: str = Field(..., description="Parent fact ID")
    child_fact_id: str = Field(..., description="Child fact ID")
    relation_type: str = Field("child", description="Relation type")


# Knowledge API Request Models


class CreateKnowledgeBaseRequest(BaseModel):
    """Request model for creating a knowledge base."""

    userid: str = Field(..., description="User ID")
    name: str = Field(..., description="Knowledge base name")
    kb_id: str | None = Field(None, description="Custom KB ID")


class ListKnowledgeBasesRequest(BaseModel):
    """Request model for listing knowledge bases."""

    userid: str = Field(..., description="User ID")


class AddKnowledgeRequest(BaseModel):
    """Request model for adding facts to a knowledge base."""

    userid: str = Field(..., description="User ID")
    kb_id: str = Field(..., description="Knowledge base ID")
    facts: list[dict[str, Any]] = Field(..., description="Facts to add")


class GetKnowledgeRequest(BaseModel):
    """Request model for retrieving facts."""

    userid: str = Field(..., description="User ID")
    kb_id: str = Field(..., description="Knowledge base ID")
    fact_id: str | None = Field(None, description="Specific fact ID")
    subtree: bool = Field(False, description="Include subtree")
    query: str | None = Field(None, description="Search query")
    limit: int = Field(50, ge=1, le=1000, description="Max facts to return")


class DeleteKnowledgeRequest(BaseModel):
    """Request model for deleting facts."""

    userid: str = Field(..., description="User ID")
    kb_id: str = Field(..., description="Knowledge base ID")
    fact_id: str = Field(..., description="Fact ID to delete")
    cascade: bool = Field(False, description="Delete descendants")


class IngestKnowledgeRequest(BaseModel):
    """Request model for ingesting knowledge from GCS."""

    userid: str = Field(..., description="User ID")
    kb_id: str = Field(..., description="Knowledge base ID")
    details: dict[str, str] = Field(..., description="Must include bucketUri")
    projecttags: list[str] = Field(default_factory=list, description="Tags for facts")
