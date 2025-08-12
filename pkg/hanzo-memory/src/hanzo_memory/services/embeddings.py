"""Embedding service using FastEmbed or LanceDB."""

from typing import Optional, Union

import numpy as np
from structlog import get_logger

from ..config import settings

logger = get_logger()

# Import backend-specific implementations
try:
    from fastembed import TextEmbedding

    FASTEMBED_AVAILABLE = True
except ImportError:
    FASTEMBED_AVAILABLE = False
    logger.warning("FastEmbed not available")

try:
    import importlib.util

    if importlib.util.find_spec("hanzo_memory.services.embeddings_lancedb") is not None:
        LANCEDB_AVAILABLE = True
    else:
        LANCEDB_AVAILABLE = False
        logger.warning("LanceDB embeddings not available")
except ImportError:
    LANCEDB_AVAILABLE = False
    logger.warning("LanceDB embeddings not available")


class EmbeddingService:
    """Service for generating embeddings using FastEmbed."""

    def __init__(self, model_name: Optional[str] = None):
        """Initialize the embedding service."""
        self.model_name = model_name or settings.embedding_model
        self._model = None
        logger.info(f"Initializing embedding service with model: {self.model_name}")

    @property
    def model(self):
        """Lazy load the embedding model."""
        if self._model is None:
            if not FASTEMBED_AVAILABLE:
                raise RuntimeError("FastEmbed is not available")
            logger.info(f"Loading embedding model: {self.model_name}")
            self._model = TextEmbedding(model_name=self.model_name)
            logger.info(f"Model {self.model_name} loaded successfully")
        return self._model

    def embed_text(self, text: Union[str, list[str]]) -> list[list[float]]:
        """
        Generate embeddings for text.

        Args:
            text: Single text string or list of text strings

        Returns:
            List of embedding vectors
        """
        if isinstance(text, str):
            text = [text]

        # Generate embeddings
        embeddings = list(self.model.embed(text))

        # Convert numpy arrays to lists
        return [emb.tolist() for emb in embeddings]

    def embed_single(self, text: str) -> list[float]:
        """
        Generate embedding for a single text.

        Args:
            text: Text string

        Returns:
            Embedding vector
        """
        embeddings = self.embed_text(text)
        return embeddings[0]

    def embed_batch(
        self,
        texts: list[str],
        batch_size: int = 32,
        show_progress: bool = False,
    ) -> list[list[float]]:
        """
        Generate embeddings for a batch of texts.

        Args:
            texts: List of text strings
            batch_size: Batch size for processing
            show_progress: Whether to show progress bar

        Returns:
            List of embedding vectors
        """
        if not texts:
            return []

        all_embeddings = []

        # Process in batches
        for i in range(0, len(texts), batch_size):
            batch = texts[i : i + batch_size]
            embeddings = self.embed_text(batch)
            all_embeddings.extend(embeddings)

            if show_progress and i > 0:
                logger.info(f"Processed {i + len(batch)}/{len(texts)} texts")

        return all_embeddings

    def compute_similarity(
        self,
        query_embedding: list[float],
        embeddings: list[list[float]],
        metric: str = "cosine",
    ) -> list[float]:
        """
        Compute similarity between query embedding and a list of embeddings.

        Args:
            query_embedding: Query embedding vector
            embeddings: List of embedding vectors to compare against
            metric: Similarity metric ("cosine", "dot", "euclidean")

        Returns:
            List of similarity scores
        """
        if not embeddings:
            return []

        query = np.array(query_embedding)
        vectors = np.array(embeddings)

        if metric == "cosine":
            # Normalize vectors for cosine similarity
            query_norm = query / np.linalg.norm(query)
            vectors_norm = vectors / np.linalg.norm(vectors, axis=1, keepdims=True)
            similarities = np.dot(vectors_norm, query_norm)
        elif metric == "dot":
            similarities = np.dot(vectors, query)
        elif metric == "euclidean":
            # Return negative distance so higher is better
            similarities = -np.linalg.norm(vectors - query, axis=1)
        else:
            raise ValueError(f"Unknown metric: {metric}")

        return list(similarities.tolist())  # Type hint for mypy

    def get_model_info(self) -> dict:
        """Get information about the current embedding model."""
        return {
            "model_name": self.model_name,
            "dimensions": settings.embedding_dimensions,
            "loaded": self._model is not None,
        }


# Global embedding service instance
_embedding_service: Optional[EmbeddingService] = None


def get_embedding_service() -> EmbeddingService:
    """Get or create the global embedding service."""
    global _embedding_service
    if _embedding_service is None:
        # Use LanceDB embeddings if configured
        if settings.db_backend == "lancedb" and LANCEDB_AVAILABLE:
            logger.info("Using LanceDB embedding service")
            from .embeddings_lancedb import get_lancedb_embedding_service

            # Wrap LanceDB service in standard interface
            lancedb_service = get_lancedb_embedding_service()
            _embedding_service = EmbeddingService()
            # Override methods with LanceDB implementation
            _embedding_service.embed_text = lancedb_service.embed_text
            _embedding_service.embed_single = lancedb_service.embed_single
            _embedding_service.embed_batch = lancedb_service.embed_batch
            _embedding_service.compute_similarity = lancedb_service.compute_similarity
            _embedding_service.get_model_info = lancedb_service.get_model_info
        elif FASTEMBED_AVAILABLE:
            logger.info("Using FastEmbed embedding service")
            _embedding_service = EmbeddingService()
        else:
            raise RuntimeError("No embedding backend available")
    return _embedding_service
