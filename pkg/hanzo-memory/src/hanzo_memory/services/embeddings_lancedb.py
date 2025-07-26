"""Embedding service using LanceDB's built-in embedding functions."""

from typing import Optional, Union

import numpy as np
from lancedb.embeddings import get_registry
from structlog import get_logger

from ..config import settings

logger = get_logger()


class LanceDBEmbeddingService:
    """Service for generating embeddings using LanceDB's embedding functions."""

    def __init__(self, model_name: Optional[str] = None):
        """Initialize the embedding service."""
        self.model_name = model_name or settings.embedding_model
        self._embedding_func = None
        logger.info(f"Initializing LanceDB embedding service with model: {self.model_name}")

    @property
    def embedding_func(self):
        """Lazy load the embedding function."""
        if self._embedding_func is None:
            logger.info(f"Loading embedding function: {self.model_name}")
            
            # LanceDB supports multiple embedding providers
            registry = get_registry()
            
            # Check available embedding functions
            available_funcs = list(registry.list_embedding_functions())
            logger.info(f"Available embedding functions: {available_funcs}")
            
            # Try to use the appropriate embedding function based on model name
            if "fastembed" in available_funcs:
                # Use FastEmbed if available
                try:
                    self._embedding_func = registry.get("fastembed").create(name=self.model_name)
                    logger.info("Using FastEmbed via LanceDB")
                except Exception as e:
                    logger.warning(f"Failed to use FastEmbed: {e}")
                    self._embedding_func = None
            
            if self._embedding_func is None:
                # Fall back to other providers
                if self.model_name.startswith("BAAI/") or "bge" in self.model_name:
                    # Use sentence-transformers for BAAI/BGE models
                    self._embedding_func = (
                        registry
                        .get("sentence-transformers")
                        .create(name=self.model_name)
                    )
                    logger.info("Using sentence-transformers via LanceDB")
                elif self.model_name.startswith("text-embedding") and "openai" in available_funcs:
                    # Use OpenAI for text-embedding models
                    self._embedding_func = (
                        registry
                        .get("openai")
                        .create(name=self.model_name)
                    )
                    logger.info("Using OpenAI embeddings via LanceDB")
                else:
                    # Default to sentence-transformers
                    self._embedding_func = (
                        registry
                        .get("sentence-transformers")
                        .create(name=self.model_name)
                    )
                    logger.info("Using sentence-transformers (default) via LanceDB")
            
            logger.info(f"Embedding function {self.model_name} loaded successfully")
        return self._embedding_func

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

        # Generate embeddings using LanceDB's embedding function
        embeddings = self.embedding_func.compute_source_embeddings(text)
        
        # Convert to list format
        if isinstance(embeddings, np.ndarray):
            return embeddings.tolist()
        else:
            return [emb.tolist() if isinstance(emb, np.ndarray) else emb for emb in embeddings]

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
            "dimensions": self.embedding_func.ndims() if self._embedding_func else settings.embedding_dimensions,
            "loaded": self._embedding_func is not None,
            "backend": "lancedb",
        }


# Global embedding service instance
_embedding_service: Optional[LanceDBEmbeddingService] = None


def get_lancedb_embedding_service() -> LanceDBEmbeddingService:
    """Get or create the global LanceDB embedding service."""
    global _embedding_service
    if _embedding_service is None:
        _embedding_service = LanceDBEmbeddingService()
    return _embedding_service