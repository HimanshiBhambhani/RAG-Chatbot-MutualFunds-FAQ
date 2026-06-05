"""
Retriever module for the RAG pipeline.
Wraps ChromaDB similarity search with optional fund-name re-ranking.
"""

import logging
from typing import Optional

from backend.config import TOP_K, EMBEDDING_PROVIDER
from backend.retrieval.vectorstore import VectorStore

logger = logging.getLogger(__name__)


class Retriever:
    """
    Retrieves the most relevant chunks for a user query.
    Uses cosine similarity search with optional metadata-based re-ranking.
    """

    def __init__(
        self,
        top_k: int = TOP_K,
        embedding_provider: Optional[str] = None,
    ):
        """
        Initialize the retriever.

        Args:
            top_k: Number of chunks to retrieve.
            embedding_provider: Override embedding provider (default from config).
        """
        self.top_k = top_k
        self.store = VectorStore(
            embedding_provider=embedding_provider or EMBEDDING_PROVIDER
        )
        logger.info(f"Retriever initialized (top_k={top_k})")

    def retrieve(
        self,
        query: str,
        top_k: Optional[int] = None,
        filter_metadata: Optional[dict] = None,
    ) -> list[dict]:
        """
        Retrieve relevant chunks for a query.

        Args:
            query: User's natural language question.
            top_k: Override default top_k for this query.
            filter_metadata: Optional ChromaDB where filter.

        Returns:
            List of dicts with 'text', 'metadata', 'distance' keys,
            sorted by relevance (most relevant first).
        """
        k = top_k or self.top_k

        results = self.store.search(
            query=query,
            top_k=k,
            filter_metadata=filter_metadata,
        )

        logger.info(
            f"Retrieved {len(results)} chunks for query: '{query[:50]}...'"
        )

        return results

    def retrieve_with_rerank(
        self,
        query: str,
        top_k: Optional[int] = None,
    ) -> list[dict]:
        """
        Retrieve chunks with metadata-based re-ranking.
        Boosts chunks whose fund_name appears in the query.

        Args:
            query: User's question.
            top_k: Number of final results to return.

        Returns:
            Re-ranked list of result dicts.
        """
        k = top_k or self.top_k
        # Fetch more candidates for re-ranking
        candidates = self.retrieve(query, top_k=k * 2)

        if not candidates:
            return []

        query_lower = query.lower()

        # Score boost for fund name match in query
        for result in candidates:
            fund_name = result["metadata"].get("fund_name", "").lower()
            scheme_name = result["metadata"].get("scheme_name", "").lower()

            # Boost relevance if fund name appears in query
            boost = 0.0
            if fund_name and fund_name in query_lower:
                boost = -0.3  # Lower distance = more relevant
            elif scheme_name and any(
                word in query_lower for word in scheme_name.split()[:3]
            ):
                boost = -0.15

            result["adjusted_distance"] = result["distance"] + boost

        # Sort by adjusted distance (lower = more relevant)
        candidates.sort(key=lambda x: x["adjusted_distance"])

        return candidates[:k]

    def format_context(self, results: list[dict]) -> str:
        """
        Format retrieved chunks into a context string for the LLM.

        Args:
            results: List of retrieval results.

        Returns:
            Formatted context string with chunk texts and source info.
        """
        if not results:
            return "No relevant information found."

        context_parts = []
        for i, result in enumerate(results, 1):
            meta = result["metadata"]
            fund_name = meta.get("fund_name", meta.get("scheme_name", "Unknown"))
            source_url = meta.get("source_url", "")

            context_parts.append(
                f"[Source {i}] Fund: {fund_name}\n"
                f"URL: {source_url}\n"
                f"Content: {result['text']}\n"
            )

        return "\n---\n".join(context_parts)

    def get_top_source(self, results: list[dict]) -> dict:
        """
        Get metadata from the most relevant result.

        Args:
            results: List of retrieval results.

        Returns:
            Dict with source_url, fund_name, scraped_at from top result.
        """
        if not results:
            return {"source_url": "", "fund_name": "", "scraped_at": ""}

        meta = results[0]["metadata"]
        return {
            "source_url": meta.get("source_url", ""),
            "fund_name": meta.get("fund_name", meta.get("scheme_name", "")),
            "scraped_at": meta.get("scraped_at", ""),
        }
