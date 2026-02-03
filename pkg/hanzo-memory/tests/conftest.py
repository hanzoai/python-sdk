"""Pytest configuration and fixtures."""

import tempfile
from collections.abc import Generator
from pathlib import Path
from unittest.mock import MagicMock, patch

import polars as pl
import pytest
from fastapi.testclient import TestClient

from hanzo_memory.config import settings
from hanzo_memory.db.client import InfinityClient
from hanzo_memory.db import reset_db_client
from hanzo_memory.services import reset_memory_service
from hanzo_memory.server import app


@pytest.fixture(autouse=True)
def test_settings(monkeypatch):
    """Configure test settings."""
    # Reset any cached clients/services before each test
    reset_db_client()
    reset_memory_service()

    # Use temporary directory for testing
    with tempfile.TemporaryDirectory() as tmpdir:
        monkeypatch.setattr(settings, "infinity_db_path", Path(tmpdir) / "test_db")
        monkeypatch.setattr(settings, "disable_auth", True)
        monkeypatch.setattr(settings, "llm_model", "gpt-3.5-turbo")
        yield

    # Reset again after test
    reset_db_client()
    reset_memory_service()


@pytest.fixture(autouse=True)
def mock_embedding_model():
    """Mock the embedding model to avoid downloads during tests."""
    with patch("fastembed.TextEmbedding") as mock_cls:
        # Create a mock instance
        mock_instance = MagicMock()

        # Mock the embed method to return fixed embeddings
        def mock_embed(texts):
            if isinstance(texts, str):
                texts = [texts]
            # Return 384-dimensional vectors (one for each text)
            for _ in texts:
                yield [0.1] * 384

        mock_instance.embed = mock_embed
        mock_cls.return_value = mock_instance

        yield mock_instance


@pytest.fixture(autouse=True)
def mock_litellm_completion():
    """Mock LiteLLM completion to avoid API calls during tests."""
    with patch("litellm.completion") as mock_completion:
        # Create mock response
        mock_response = MagicMock()
        mock_response.choices = [
            MagicMock(message=MagicMock(content="Mocked LLM response"))
        ]
        mock_completion.return_value = mock_response
        yield mock_completion


@pytest.fixture
def client() -> Generator[TestClient, None, None]:
    """Create test client."""
    with TestClient(app) as test_client:
        yield test_client


@pytest.fixture
def db_client(test_settings) -> Generator[InfinityClient, None, None]:
    """Create test database client."""
    client = InfinityClient()
    yield client
    client.close()


@pytest.fixture
def sample_user_id() -> str:
    """Sample user ID for testing."""
    return "test_user_123"


@pytest.fixture
def sample_project_id() -> str:
    """Sample project ID for testing."""
    return "test_project_456"


@pytest.fixture
def sample_memory_content() -> str:
    """Sample memory content."""
    return "I prefer dark mode interfaces and enjoy using VS Code."


@pytest.fixture
def sample_messages() -> list:
    """Sample chat messages."""
    return [
        {"role": "user", "content": "Hello, how are you?"},
        {"role": "assistant", "content": "I'm doing well, thank you!"},
        {"role": "user", "content": "Can you help me with Python?"},
    ]


@pytest.fixture
def mock_auth():
    """Mock authentication."""
    with patch("hanzo_memory.api.auth.require_auth") as mock:
        mock.return_value = "test-api-key"
        with patch("hanzo_memory.api.auth.get_or_verify_user_id") as mock_verify:
            mock_verify.side_effect = lambda user_id, *args: user_id
            yield mock


@pytest.fixture
def mock_db_client():
    """Mock database client."""
    with patch("hanzo_memory.server.db_client") as mock:
        # Set up default mock behaviors
        mock.create_project = MagicMock()
        mock.create_knowledge_base = MagicMock()
        mock.add_fact = MagicMock()
        mock.search_facts = MagicMock(return_value=pl.DataFrame())
        mock.create_memories_table = MagicMock()
        mock.add_memory = MagicMock()
        mock.search_memories = MagicMock(return_value=pl.DataFrame())
        yield mock


@pytest.fixture
def mock_services():
    """Mock services."""
    with patch("hanzo_memory.server.embedding_service") as mock_embed:
        mock_embed.embed_text = MagicMock(return_value=[[0.1] * 384])
        services = {
            "embedding": mock_embed,
        }
        yield services
