"""Test memory API endpoints."""

from fastapi import status


class TestMemoryAPI:
    """Test memory API endpoints."""

    def test_health_check(self, client):
        """Test health check endpoint."""
        response = client.get("/health")
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["status"] == "healthy"
        assert data["service"] == "hanzo-memory"

    def test_remember_endpoint(self, client, sample_user_id, sample_memory_content):
        """Test /v1/remember endpoint."""
        request_data = {
            "userid": sample_user_id,
            "messagecontent": sample_memory_content,
            "strippii": False,
            "filterresults": False,
            "includememoryid": False,
        }

        response = client.post("/v1/remember", json=request_data)
        assert response.status_code == status.HTTP_200_OK

        data = response.json()
        assert data["user_id"] == sample_user_id
        assert data["memory_stored"] is True
        assert "relevant_memories" in data
        assert "usage_info" in data

    def test_remember_with_memory_ids(self, client, sample_user_id):
        """Test /v1/remember with memory IDs included."""
        # First, add a memory
        request_data = {
            "userid": sample_user_id,
            "messagecontent": "I love Python programming",
            "includememoryid": True,
        }

        response = client.post("/v1/remember", json=request_data)
        assert response.status_code == status.HTTP_200_OK

        # Search for similar memory
        search_data = {
            "userid": sample_user_id,
            "messagecontent": "Python is great",
            "includememoryid": True,
        }

        response = client.post("/v1/remember", json=search_data)
        assert response.status_code == status.HTTP_200_OK

        data = response.json()
        memories = data["relevant_memories"]
        if memories:
            assert isinstance(memories[0], dict)
            assert "content" in memories[0]
            assert "memoryId" in memories[0]

    def test_add_memories(self, client, sample_user_id):
        """Test /v1/memories/add endpoint."""
        # Test with single memory
        request_data = {
            "userid": sample_user_id,
            "memoriestoadd": "Single memory content",
        }

        response = client.post("/v1/memories/add", json=request_data)
        assert response.status_code == status.HTTP_200_OK

        data = response.json()
        assert data["userid"] == sample_user_id
        assert data["added_count"] == 1
        assert len(data["memory_ids"]) == 1

        # Test with multiple memories
        request_data = {
            "userid": sample_user_id,
            "memoriestoadd": [
                "First memory",
                "Second memory",
                "Third memory",
            ],
        }

        response = client.post("/v1/memories/add", json=request_data)
        assert response.status_code == status.HTTP_200_OK

        data = response.json()
        assert data["added_count"] == 3
        assert len(data["memory_ids"]) == 3

    def test_get_memories(self, client, sample_user_id):
        """Test /v1/memories/get endpoint."""
        # Without memoryid, API returns 400
        request_data = {
            "userid": sample_user_id,
            "limit": 10,
        }
        response = client.post("/v1/memories/get", json=request_data)
        assert response.status_code == status.HTTP_400_BAD_REQUEST

        # With memoryid but non-existent, returns 404
        request_data = {
            "userid": sample_user_id,
            "memoryid": "non-existent-memory",
        }
        response = client.post("/v1/memories/get", json=request_data)
        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_delete_user_memories(self, client, sample_user_id):
        """Test /v1/user/delete endpoint."""
        # Test without confirmation
        request_data = {
            "userid": sample_user_id,
            "confirmdelete": False,
        }

        response = client.post("/v1/user/delete", json=request_data)
        assert response.status_code == status.HTTP_400_BAD_REQUEST

        # Test with confirmation
        request_data["confirmdelete"] = True
        response = client.post("/v1/user/delete", json=request_data)
        assert response.status_code == status.HTTP_200_OK

        data = response.json()
        assert data["userid"] == sample_user_id
        assert "deleted_count" in data
