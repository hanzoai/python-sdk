"""Base models for Hanzo Memory Service."""

from datetime import datetime

from pydantic import BaseModel, Field


class TimestampedModel(BaseModel):
    """Base model with timestamps."""

    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)


class UserScopedModel(BaseModel):
    """Base model for user-scoped resources."""

    user_id: str = Field(..., description="User ID")


class ProjectScopedModel(UserScopedModel):
    """Base model for project-scoped resources."""

    project_id: str = Field(..., description="Project ID")
