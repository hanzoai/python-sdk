"""Tests for embedding service edge cases."""

import pytest

from hanzo_memory.services.embeddings import EmbeddingService


class TestEmbeddingsEdgeCases:
    """Test embedding service edge cases."""

    @pytest.fixture
    def embedding_service(self):
        """Create embedding service."""
        return EmbeddingService()

    def test_compute_similarity_dot_product(self, embedding_service):
        """Test compute similarity with dot product metric."""
        query = [1.0, 2.0, 3.0]
        embeddings = [
            [1.0, 2.0, 3.0],  # Same as query
            [3.0, 2.0, 1.0],  # Different
        ]

        scores = embedding_service.compute_similarity(query, embeddings, metric="dot")

        assert len(scores) == 2
        assert scores[0] > scores[1]  # First should have higher dot product

    def test_compute_similarity_euclidean(self, embedding_service):
        """Test compute similarity with euclidean metric."""
        query = [1.0, 2.0, 3.0]
        embeddings = [
            [1.0, 2.0, 3.0],  # Same as query (distance = 0)
            [4.0, 5.0, 6.0],  # Different
        ]

        scores = embedding_service.compute_similarity(
            query, embeddings, metric="euclidean"
        )

        assert len(scores) == 2
        # Euclidean returns negative distance, so same vector should have highest score
        assert scores[0] > scores[1]

    def test_compute_similarity_empty_embeddings(self, embedding_service):
        """Test compute similarity with empty embeddings."""
        query = [1.0, 2.0, 3.0]
        embeddings = []

        scores = embedding_service.compute_similarity(query, embeddings)

        assert scores == []

    def test_compute_similarity_invalid_metric(self, embedding_service):
        """Test compute similarity with invalid metric."""
        query = [1.0, 2.0, 3.0]
        embeddings = [[1.0, 2.0, 3.0]]

        with pytest.raises(ValueError, match="Unknown metric"):
            embedding_service.compute_similarity(query, embeddings, metric="invalid")
