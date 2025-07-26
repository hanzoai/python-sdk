"""Tests for Knowledge Base API endpoints."""


import polars as pl
import pytest
from fastapi.testclient import TestClient

from hanzo_memory.server import app


class TestKnowledgeAPI:
    """Test Knowledge Base API endpoints."""

    @pytest.fixture(autouse=True)
    def setup(self, mock_auth, mock_db_client, mock_services):
        """Set up test client and mocks."""
        self.client = TestClient(app)
        self.headers = {"Authorization": "Bearer test-token"}
        self.mock_db = mock_db_client
        self.mock_embedding_service = mock_services["embedding"]

    def test_create_knowledge_base(self):
        """Test creating a knowledge base."""
        self.mock_db.create_knowledge_base.return_value = {
            "kb_id": "kb123",
            "name": "Test KB",
        }

        response = self.client.post(
            "/v1/kb/create",
            json={
                "userid": "user123",
                "name": "Test KB",
                "kb_id": "kb123",
            },
            headers=self.headers,
        )

        assert response.status_code == 200
        data = response.json()
        assert data["kb_id"] == "kb123"
        assert "Test KB" in data["message"]

        # Verify DB calls
        self.mock_db.create_knowledge_base.assert_called_once()
        call_args = self.mock_db.create_knowledge_base.call_args[1]
        assert call_args["kb_id"] == "kb123"
        assert call_args["user_id"] == "user123"
        assert call_args["name"] == "Test KB"

    def test_create_knowledge_base_default_project(self):
        """Test creating KB with default project."""
        # Mock project creation to raise (already exists)
        self.mock_db.create_project.side_effect = Exception("Already exists")
        self.mock_db.create_knowledge_base.return_value = {"kb_id": "kb123"}

        response = self.client.post(
            "/v1/kb/create",
            json={
                "userid": "user123",
                "name": "Test KB",
            },
            headers=self.headers,
        )

        assert response.status_code == 200

        # Verify default project was attempted
        self.mock_db.create_project.assert_called_once()
        project_args = self.mock_db.create_project.call_args[1]
        assert project_args["project_id"] == "default-user123"
        assert project_args["user_id"] == "user123"

    def test_list_knowledge_bases(self):
        """Test listing knowledge bases."""
        response = self.client.get(
            "/v1/kb/list",
            params={"userid": "user123"},
            headers=self.headers,
        )

        assert response.status_code == 200
        data = response.json()
        assert data["userid"] == "user123"
        assert "knowledge_bases" in data
        assert data["total"] == 0

    def test_add_facts(self):
        """Test adding facts to a knowledge base."""
        self.mock_embedding_service.embed_text.return_value = [[0.1] * 384]
        self.mock_db.add_fact.return_value = {"fact_id": "fact123"}

        response = self.client.post(
            "/v1/kb/facts/add",
            json={
                "userid": "user123",
                "kb_id": "kb123",
                "facts": [
                    {
                        "content": "Test fact 1",
                        "metadata": {"type": "test"},
                    },
                    {
                        "content": "Test fact 2",
                        "parent_id": "fact123",
                    },
                ],
            },
            headers=self.headers,
        )

        assert response.status_code == 200
        data = response.json()
        assert data["kb_id"] == "kb123"
        assert data["facts_added"] == 2
        assert len(data["facts"]) == 2

        # Verify embeddings were generated
        assert self.mock_embedding_service.embed_text.call_count == 2

        # Verify facts were added
        assert self.mock_db.add_fact.call_count == 2

    def test_get_facts_with_query(self):
        """Test searching facts with a query."""
        # Mock search results
        mock_df = pl.DataFrame({
            "fact_id": ["fact1", "fact2"],
            "content": ["Fact 1", "Fact 2"],
            "parent_id": ["", "parent1"],
            "metadata": ['{"type": "test"}', '{"type": "example"}'],
            "_similarity": [0.95, 0.85],
        })

        self.mock_db.search_facts.return_value = mock_df
        self.mock_embedding_service.embed_text.return_value = [[0.2] * 384]

        response = self.client.post(
            "/v1/kb/facts/get",
            json={
                "userid": "user123",
                "kb_id": "kb123",
                "query": "test query",
                "limit": 10,
            },
            headers=self.headers,
        )

        assert response.status_code == 200
        data = response.json()
        assert data["kb_id"] == "kb123"
        assert len(data["facts"]) == 2
        assert data["facts"][0]["fact_id"] == "fact1"
        assert data["facts"][0]["similarity_score"] == 0.95

        # Verify search was called
        self.mock_db.search_facts.assert_called_once()
        search_args = self.mock_db.search_facts.call_args[1]
        assert search_args["kb_id"] == "kb123"
        assert search_args["limit"] == 10

    def test_get_facts_without_query(self):
        """Test getting facts without a search query."""
        response = self.client.post(
            "/v1/kb/facts/get",
            json={
                "userid": "user123",
                "kb_id": "kb123",
            },
            headers=self.headers,
        )

        assert response.status_code == 200
        data = response.json()
        assert data["kb_id"] == "kb123"
        assert data["facts"] == []
        assert data["total"] == 0

    def test_delete_fact(self):
        """Test deleting a fact."""
        response = self.client.post(
            "/v1/kb/facts/delete",
            json={
                "userid": "user123",
                "kb_id": "kb123",
                "fact_id": "fact123",
                "cascade": True,
            },
            headers=self.headers,
        )

        assert response.status_code == 200
        data = response.json()
        assert data["kb_id"] == "kb123"
        assert data["fact_id"] == "fact123"
        assert data["deleted"] is True
        assert data["cascade"] is True

    def test_knowledge_base_error_handling(self):
        """Test error handling in knowledge base operations."""
        self.mock_db.create_knowledge_base.side_effect = Exception("DB Error")

        response = self.client.post(
            "/v1/kb/create",
            json={
                "userid": "user123",
                "name": "Test KB",
            },
            headers=self.headers,
        )

        assert response.status_code == 500
        data = response.json()
        assert "detail" in data
        assert "DB Error" in data["detail"]
