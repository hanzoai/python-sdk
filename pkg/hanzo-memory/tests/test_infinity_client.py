"""Test InfinityDB client."""

import uuid


class TestInfinityClient:
    """Test InfinityDB client."""

    def test_client_initialization(self, db_client):
        """Test client initialization."""
        assert db_client is not None
        assert hasattr(db_client, "infinity")

    def test_create_project(self, db_client, sample_user_id):
        """Test project creation."""
        # Ensure projects table exists
        db_client.create_projects_table()

        project_id = f"test_project_{uuid.uuid4().hex[:8]}"

        project = db_client.create_project(
            project_id=project_id,
            user_id=sample_user_id,
            name="Test Project",
            description="A test project",
            metadata={"test": True},
        )

        assert project["project_id"] == project_id
        assert project["user_id"] == sample_user_id
        assert project["name"] == "Test Project"
        assert "created_at" in project

    def test_memory_operations(self, db_client, sample_user_id, sample_project_id):
        """Test memory CRUD operations."""
        # Create memories table
        db_client.create_memories_table(sample_user_id)

        # Add a memory
        memory_id = f"mem_{uuid.uuid4().hex[:8]}"
        embedding = [0.1] * 384  # Mock embedding

        memory = db_client.add_memory(
            memory_id=memory_id,
            user_id=sample_user_id,
            project_id=sample_project_id,
            content="Test memory content",
            embedding=embedding,
            metadata={"source": "test"},
            importance=7.5,
        )

        assert memory["memory_id"] == memory_id
        assert memory["content"] == "Test memory content"
        assert memory["importance"] == 7.5

    def test_memory_search(self, db_client, sample_user_id, sample_project_id):
        """Test memory search functionality."""
        # Create memories table
        db_client.create_memories_table(sample_user_id)

        # Add some memories
        memories_data = [
            ("Python programming is fun", [0.8, 0.2] + [0.1] * 382),
            ("JavaScript is also great", [0.2, 0.8] + [0.1] * 382),
            ("I love coding", [0.5, 0.5] + [0.1] * 382),
        ]

        for i, (content, embedding) in enumerate(memories_data):
            db_client.add_memory(
                memory_id=f"mem_{i}",
                user_id=sample_user_id,
                project_id=sample_project_id,
                content=content,
                embedding=embedding,
            )

        # Search for Python-related memories
        query_embedding = [0.9, 0.1] + [0.1] * 382
        results = db_client.search_memories(
            user_id=sample_user_id,
            query_embedding=query_embedding,
            limit=2,
        )

        assert not results.is_empty()
        assert len(results) <= 2

    def test_knowledge_base_operations(
        self, db_client, sample_user_id, sample_project_id
    ):
        """Test knowledge base operations."""
        # Ensure knowledge bases table exists
        db_client.create_knowledge_bases_table()

        kb_id = f"kb_{uuid.uuid4().hex[:8]}"

        # Create knowledge base
        kb = db_client.create_knowledge_base(
            kb_id=kb_id,
            user_id=sample_user_id,
            project_id=sample_project_id,
            name="Test Knowledge Base",
            description="Testing KB",
        )

        assert kb["kb_id"] == kb_id
        assert kb["name"] == "Test Knowledge Base"

        # Add a fact
        fact_id = f"fact_{uuid.uuid4().hex[:8]}"
        embedding = [0.1] * 384

        fact = db_client.add_fact(
            fact_id=fact_id,
            kb_id=kb_id,
            content="Python was created by Guido van Rossum",
            embedding=embedding,
            metadata={"category": "history"},
        )

        assert fact["fact_id"] == fact_id
        assert fact["content"] == "Python was created by Guido van Rossum"

    def test_chat_operations(self, db_client, sample_user_id, sample_project_id):
        """Test chat operations."""
        # Create chats table
        db_client.create_chats_table(sample_user_id)

        # Add chat messages
        session_id = f"session_{uuid.uuid4().hex[:8]}"
        messages = [
            ("user", "Hello, how are you?"),
            ("assistant", "I'm doing well, thank you!"),
        ]

        for i, (role, content) in enumerate(messages):
            embedding = [0.1] * 384
            chat = db_client.add_chat_message(
                chat_id=f"chat_{i}",
                user_id=sample_user_id,
                project_id=sample_project_id,
                session_id=session_id,
                role=role,
                content=content,
                embedding=embedding,
            )

            assert chat["role"] == role
            assert chat["content"] == content

        # Get chat history
        history = db_client.get_chat_history(
            user_id=sample_user_id,
            session_id=session_id,
        )

        assert not history.is_empty()
