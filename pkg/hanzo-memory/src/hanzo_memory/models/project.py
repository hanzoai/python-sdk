"""Project models."""

from typing import Any

from pydantic import BaseModel, Field

from .base import TimestampedModel, UserScopedModel


class ProjectBase(BaseModel):
    """Base project model."""

    name: str = Field(..., description="Project name")
    description: str = Field("", description="Project description")
    metadata: dict[str, Any] = Field(
        default_factory=dict, description="Additional metadata"
    )


class ProjectCreate(ProjectBase):
    """Model for creating a project."""

    pass


class ProjectUpdate(BaseModel):
    """Model for updating a project."""

    name: str | None = None
    description: str | None = None
    metadata: dict[str, Any] | None = None


class Project(ProjectBase, UserScopedModel, TimestampedModel):
    """Complete project model."""

    project_id: str = Field(..., description="Project ID")
    knowledge_base_ids: list[str] = Field(
        default_factory=list, description="Associated knowledge base IDs"
    )
    memory_count: int = Field(0, description="Number of memories in project")

    model_config = {"from_attributes": True}


class ProjectList(BaseModel):
    """Project list response."""

    projects: list[Project] = Field(..., description="List of projects")
    total: int = Field(..., description="Total number of projects")
    page: int = Field(1, description="Current page")
    per_page: int = Field(50, description="Items per page")
