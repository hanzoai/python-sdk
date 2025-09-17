"""Hanzo Memory Service - AI memory and knowledge management."""

__version__ = "1.0.1"
__author__ = "Hanzo Industries Inc."
__email__ = "dev@hanzo.ai"

# Import models - these are always needed
from .models.knowledge import Fact, FactCreate, KnowledgeBase
from .models.memory import Memory, MemoryCreate, MemoryResponse
from .models.project import Project, ProjectCreate

# Import database factory for getting the configured client
from .db.factory import get_db_client

__all__ = [
    "get_db_client",
    "Memory",
    "MemoryCreate",
    "MemoryResponse",
    "KnowledgeBase",
    "Fact",
    "FactCreate",
    "Project",
    "ProjectCreate",
]
