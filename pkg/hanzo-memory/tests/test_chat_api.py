"""Tests for Chat API endpoints."""


import polars as pl
import pytest
from fastapi.testclient import TestClient

from hanzo_memory.server import app


class TestChatAPI:
    """Test Chat API endpoints."""

    @pytest.fixture(autouse=True)
    def setup(self, mock_auth, mock_db_client, mock_services):
        """Set up test client and mocks."""
        self.client = TestClient(app)
        self.headers = {"Authorization": "Bearer test-token"}
        self.mock_db = mock_db_client
        self.mock_embedding_service = mock_services["embedding"]

    def test_create_chat_session(self):
        """Test creating a chat session."""
        response = self.client.post(
            "/v1/chat/sessions/create",
            json={
                "userid": "user123",
                "session_id": "session123",
                "project_id": "proj123",
            },
            headers=self.headers,
        )

        assert response.status_code == 200
        data = response.json()
        assert data["session_id"] == "session123"
        assert data["userid"] == "user123"
        assert data["project_id"] == "proj123"
        assert data["created"] is True

        # Verify chat table was created
        self.mock_db.create_chats_table.assert_called_once_with("user123")

    def test_create_chat_session_auto_ids(self):
        """Test creating a chat session with auto-generated IDs."""
        response = self.client.post(
            "/v1/chat/sessions/create",
            json={"userid": "user123"},
            headers=self.headers,
        )

        assert response.status_code == 200
        data = response.json()
        assert "session_id" in data
        assert data["userid"] == "user123"
        assert data["project_id"] == "default-user123"

    def test_add_chat_message(self):
        """Test adding a chat message."""
        # Mock empty search results (no duplicates)
        self.mock_db.search_chats.return_value = pl.DataFrame()
        self.mock_db.add_chat_message.return_value = {"chat_id": "msg123"}

        response = self.client.post(
            "/v1/chat/messages/add",
            json={
                "userid": "user123",
                "session_id": "session123",
                "role": "user",
                "content": "Hello, how are you?",
                "metadata": {"timestamp": "2023-01-01T12:00:00Z"},
            },
            headers=self.headers,
        )

        assert response.status_code == 200
        data = response.json()
        assert "chat_id" in data
        assert data["session_id"] == "session123"
        assert data["duplicate"] is False

        # Verify embedding was generated
        self.mock_embedding_service.embed_text.assert_called_once_with(
            "Hello, how are you?"
        )

        # Verify message was added
        self.mock_db.add_chat_message.assert_called_once()

    def test_add_duplicate_chat_message(self):
        """Test adding a duplicate chat message."""
        # Mock search results with duplicate
        mock_df = pl.DataFrame({
            "chat_id": ["existing123"],
            "content": ["Hello, how are you?"],
            "role": ["user"],
            "_similarity": [0.995],
        })
        self.mock_db.search_chats.return_value = mock_df

        response = self.client.post(
            "/v1/chat/messages/add",
            json={
                "userid": "user123",
                "session_id": "session123",
                "role": "user",
                "content": "Hello, how are you?",
            },
            headers=self.headers,
        )

        assert response.status_code == 200
        data = response.json()
        assert data["chat_id"] == "existing123"
        assert data["duplicate"] is True

        # Verify message was NOT added
        self.mock_db.add_chat_message.assert_not_called()

    def test_get_chat_messages(self):
        """Test getting chat messages for a session."""
        # Mock chat history
        mock_df = pl.DataFrame({
            "chat_id": ["msg1", "msg2", "msg3"],
            "role": ["user", "assistant", "user"],
            "content": ["Hello", "Hi there!", "How are you?"],
            "metadata": ['{}', '{"model": "gpt-4"}', '{}'],
            "created_at": ["2023-01-01T12:00:00", "2023-01-01T12:01:00", "2023-01-01T12:02:00"],
        })
        self.mock_db.get_chat_history.return_value = mock_df

        response = self.client.get(
            "/v1/chat/sessions/session123/messages",
            params={"userid": "user123", "limit": 100},
            headers=self.headers,
        )

        assert response.status_code == 200
        data = response.json()
        assert data["session_id"] == "session123"
        assert len(data["messages"]) == 3
        assert data["total"] == 3

        # Check message order
        assert data["messages"][0]["content"] == "Hello"
        assert data["messages"][1]["content"] == "Hi there!"
        assert data["messages"][2]["content"] == "How are you?"

    def test_search_chat_messages(self):
        """Test searching chat messages."""
        # Mock search results
        mock_df = pl.DataFrame({
            "chat_id": ["msg1", "msg2"],
            "session_id": ["session1", "session2"],
            "role": ["user", "assistant"],
            "content": ["Tell me about Python", "Python is a programming language"],
            "_similarity": [0.95, 0.92],
            "created_at": ["2023-01-01T12:00:00", "2023-01-01T13:00:00"],
        })
        self.mock_db.search_chats.return_value = mock_df

        response = self.client.post(
            "/v1/chat/search",
            params={
                "query": "Python programming",
                "userid": "user123",
                "limit": 10,
            },
            headers=self.headers,
        )

        assert response.status_code == 200
        data = response.json()
        assert data["query"] == "Python programming"
        assert len(data["messages"]) == 2
        assert data["messages"][0]["similarity_score"] == 0.95
        assert "Python" in data["messages"][0]["content"]

        # Verify search was called
        self.mock_db.search_chats.assert_called_once()
        search_args = self.mock_db.search_chats.call_args[1]
        assert search_args["user_id"] == "user123"
        assert search_args["limit"] == 10

    def test_search_chat_with_filters(self):
        """Test searching chat messages with filters."""
        self.mock_db.search_chats.return_value = pl.DataFrame()

        response = self.client.post(
            "/v1/chat/search",
            params={
                "query": "test query",
                "userid": "user123",
                "project_id": "proj123",
                "session_id": "session123",
                "limit": 5,
            },
            headers=self.headers,
        )

        assert response.status_code == 200

        # Verify filters were passed
        search_args = self.mock_db.search_chats.call_args[1]
        assert search_args["project_id"] == "proj123"
        assert search_args["session_id"] == "session123"

    def test_chat_error_handling(self):
        """Test error handling in chat operations."""
        self.mock_db.create_chats_table.side_effect = Exception("DB Error")

        response = self.client.post(
            "/v1/chat/sessions/create",
            json={"userid": "user123"},
            headers=self.headers,
        )

        assert response.status_code == 500
        data = response.json()
        assert "detail" in data
        assert "DB Error" in data["detail"]
