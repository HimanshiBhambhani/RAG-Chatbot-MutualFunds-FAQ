"""
Embedding generation for mutual fund chunks.
Supports Google Gemini text-embedding-004 (primary), ChromaDB default (local ONNX),
and HuggingFace sentence-transformers (fallback).
"""

import logging
from typing import Optional

from backend.config import EMBEDDING_PROVIDER, GEMINI_EMBEDDING_MODEL, GOOGLE_API_KEY

logger = logging.getLogger(__name__)


class ChromaDefaultEmbeddings:
    """
    Wrapper around ChromaDB's built-in DefaultEmbeddingFunction
    that provides a LangChain-compatible interface.
    Uses all-MiniLM-L6-v2 via ONNX runtime (fully local, no downloads needed).
    """

    def __init__(self):
        from chromadb.utils.embedding_functions import DefaultEmbeddingFunction
        self._ef = DefaultEmbeddingFunction()
        logger.info("Initialized ChromaDB default embeddings (all-MiniLM-L6-v2 ONNX)")

    def embed_documents(self, texts: list[str]) -> list[list[float]]:
        """Embed a list of documents."""
        results = self._ef(texts)
        return [[float(x) for x in emb] for emb in results]

    def embed_query(self, query: str) -> list[float]:
        """Embed a single query."""
        results = self._ef([query])
        return [float(x) for x in results[0]]


class EmbeddingManager:
    """Manages embedding generation with provider switching."""

    def __init__(self, provider: Optional[str] = None):
        """
        Initialize embedding manager.

        Args:
            provider: "gemini" or "huggingface". Defaults to config value.
        """
        self.provider = provider or EMBEDDING_PROVIDER
        self._embeddings = None

    @property
    def embeddings(self):
        """Lazy-load the embedding model."""
        if self._embeddings is None:
            self._embeddings = self._create_embeddings()
        return self._embeddings

    def _create_embeddings(self):
        """Create the embedding instance based on provider."""
        if self.provider == "gemini":
            return self._create_gemini_embeddings()
        elif self.provider == "huggingface":
            return self._create_huggingface_embeddings()
        elif self.provider == "chroma_default":
            return ChromaDefaultEmbeddings()
        else:
            raise ValueError(f"Unknown embedding provider: {self.provider}")

    def _create_gemini_embeddings(self):
        """Create Google Gemini embeddings."""
        from langchain_google_genai import GoogleGenerativeAIEmbeddings

        if not GOOGLE_API_KEY:
            raise ValueError(
                "GOOGLE_API_KEY not set. Add it to your .env file."
            )

        logger.info(f"Initializing Gemini embeddings: {GEMINI_EMBEDDING_MODEL}")
        return GoogleGenerativeAIEmbeddings(
            model=GEMINI_EMBEDDING_MODEL,
            google_api_key=GOOGLE_API_KEY,
        )

    def _create_huggingface_embeddings(self):
        """Create HuggingFace sentence-transformers embeddings (local, free)."""
        from langchain_community.embeddings import HuggingFaceEmbeddings

        model_name = "sentence-transformers/all-MiniLM-L6-v2"
        logger.info(f"Initializing HuggingFace embeddings: {model_name}")
        return HuggingFaceEmbeddings(
            model_name=model_name,
            model_kwargs={"device": "cpu"},
            encode_kwargs={"normalize_embeddings": True},
        )

    def embed_texts(self, texts: list[str]) -> list[list[float]]:
        """
        Generate embeddings for a list of texts.

        Args:
            texts: List of text strings to embed.

        Returns:
            List of embedding vectors.
        """
        logger.info(f"Embedding {len(texts)} texts with {self.provider}...")
        return self.embeddings.embed_documents(texts)

    def embed_query(self, query: str) -> list[float]:
        """
        Generate embedding for a single query.

        Args:
            query: Query text to embed.

        Returns:
            Embedding vector.
        """
        return self.embeddings.embed_query(query)


def get_embedding_function(provider: Optional[str] = None):
    """
    Get a LangChain-compatible embedding function for ChromaDB.

    Args:
        provider: "gemini" or "huggingface". Defaults to config.

    Returns:
        LangChain Embeddings instance.
    """
    manager = EmbeddingManager(provider)
    return manager.embeddings
