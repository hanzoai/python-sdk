"""Test embedding service."""

import pytest

from hanzo_memory.services.embeddings import EmbeddingService


class TestEmbeddingService:
    """Test embedding service."""

    @pytest.fixture
    def embedding_service(self):
        """Create embedding service."""
        return EmbeddingService()

    def test_embed_single(self, embedding_service):
        """Test single text embedding."""
        text = "Hello, world!"
        embedding = embedding_service.embed_single(text)

        assert isinstance(embedding, list)
        assert len(embedding) == 384  # BGE small dimension
        assert all(isinstance(x, float) for x in embedding)

    def test_embed_batch(self, embedding_service):
        """Test batch text embedding."""
        texts = ["Hello", "World", "Test"]
        embeddings = embedding_service.embed_batch(texts)

        assert len(embeddings) == 3
        assert all(len(emb) == 384 for emb in embeddings)

    def test_compute_similarity_cosine(self, embedding_service):
        """Test cosine similarity computation."""
        # Create simple test embeddings
        query = [1.0, 0.0, 0.0]
        embeddings = [
            [1.0, 0.0, 0.0],  # Same as query
            [0.0, 1.0, 0.0],  # Orthogonal
            [-1.0, 0.0, 0.0],  # Opposite
        ]

        similarities = embedding_service.compute_similarity(
            query, embeddings, metric="cosine"
        )

        assert len(similarities) == 3
        assert similarities[0] > 0.99  # Very similar
        assert abs(similarities[1]) < 0.01  # Orthogonal
        assert similarities[2] < -0.99  # Opposite

    def test_empty_batch(self, embedding_service):
        """Test embedding empty batch."""
        embeddings = embedding_service.embed_batch([])
        assert embeddings == []

    def test_model_info(self, embedding_service):
        """Test getting model info."""
        info = embedding_service.get_model_info()

        assert info["model_name"] == "BAAI/bge-small-en-v1.5"
        assert info["dimensions"] == 384
        assert "loaded" in info
