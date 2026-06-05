"""
ChromaDB Vector Store for mutual fund chunks.
Handles collection management, insertion, and similarity search.
"""

import logging
from typing import Optional

import chromadb
from chromadb.config import Settings

from backend.config import CHROMA_COLLECTION_NAME, CHROMA_PERSIST_DIR
from backend.retrieval.embeddings import get_embedding_function

logger = logging.getLogger(__name__)


class VectorStore:
    """Manages the ChromaDB vector store for fund data chunks."""

    def __init__(
        self,
        persist_dir: Optional[str] = None,
        collection_name: Optional[str] = None,
        embedding_provider: Optional[str] = None,
    ):
        """
        Initialize the vector store.

        Args:
            persist_dir: Directory for ChromaDB persistence.
            collection_name: Name of the ChromaDB collection.
            embedding_provider: "gemini" or "huggingface".
        """
        self.persist_dir = persist_dir or CHROMA_PERSIST_DIR
        self.collection_name = collection_name or CHROMA_COLLECTION_NAME
        self.embedding_provider = embedding_provider

        self._client = None
        self._collection = None
        self._embedding_fn = None

    @property
    def client(self) -> chromadb.ClientAPI:
        """Lazy-load ChromaDB persistent client."""
        if self._client is None:
            logger.info(f"Initializing ChromaDB at: {self.persist_dir}")
            self._client = chromadb.PersistentClient(
                path=self.persist_dir,
                settings=Settings(anonymized_telemetry=False),
            )
        return self._client

    @property
    def collection(self) -> chromadb.Collection:
        """Get or create the ChromaDB collection."""
        if self._collection is None:
            self._collection = self.client.get_or_create_collection(
                name=self.collection_name,
                metadata={"description": "Mutual fund FAQ chunks from Groww"},
            )
            logger.info(
                f"Collection '{self.collection_name}': {self._collection.count()} documents"
            )
        return self._collection

    @property
    def embedding_fn(self):
        """Lazy-load embedding function."""
        if self._embedding_fn is None:
            self._embedding_fn = get_embedding_function(self.embedding_provider)
        return self._embedding_fn

    def add_chunks(self, chunks: list[dict], batch_size: int = 50) -> int:
        """
        Add chunks to the vector store with embeddings.

        Args:
            chunks: List of chunk dicts with 'text' and 'metadata' keys.
            batch_size: Number of chunks to embed/insert per batch.

        Returns:
            Total number of chunks added.
        """
        if not chunks:
            logger.warning("No chunks to add.")
            return 0

        # Check which chunks already exist (for resumable ingestion)
        all_ids = []
        for i in range(0, len(chunks), batch_size):
            batch = chunks[i : i + batch_size]
            for j, c in enumerate(batch):
                all_ids.append(f"{c['metadata'].get('slug', 'unknown')}_{c['metadata'].get('chunk_index', i+j)}")

        existing_ids = set()
        try:
            result = self.collection.get(ids=all_ids)
            existing_ids = set(result["ids"]) if result["ids"] else set()
        except Exception:
            pass

        total = len(chunks)
        logger.info(f"Adding {total} chunks to vector store (batch_size={batch_size})...")
        if existing_ids:
            logger.info(f"  Resuming: {len(existing_ids)} chunks already indexed, skipping them.")

        added = 0
        skipped = 0
        import time

        for i in range(0, total, batch_size):
            batch = chunks[i : i + batch_size]

            texts = [c["text"] for c in batch]
            metadatas = [self._sanitize_metadata(c["metadata"]) for c in batch]
            ids = [
                f"{c['metadata'].get('slug', 'unknown')}_{c['metadata'].get('chunk_index', i+j)}"
                for j, c in enumerate(batch)
            ]

            # Skip batch if all IDs already exist
            if all(id_ in existing_ids for id_ in ids):
                skipped += len(batch)
                logger.info(f"  Skipping batch {i//batch_size + 1} (already indexed)")
                continue

            # Generate embeddings with retry on rate limit and connection errors
            max_retries = 8
            for attempt in range(max_retries):
                try:
                    embeddings = self.embedding_fn.embed_documents(texts)
                    break
                except Exception as e:
                    err_str = str(e)
                    if "429" in err_str or "RESOURCE_EXHAUSTED" in err_str:
                        wait_time = 60 * (attempt + 1)
                        logger.warning(f"  Rate limited. Waiting {wait_time}s before retry {attempt+1}/{max_retries}...")
                        time.sleep(wait_time)
                    elif "Connection" in err_str or "ReadError" in err_str or "reset by peer" in err_str or "timeout" in err_str.lower():
                        wait_time = 30 * (attempt + 1)
                        logger.warning(f"  Connection error. Waiting {wait_time}s before retry {attempt+1}/{max_retries}...")
                        time.sleep(wait_time)
                    else:
                        raise
            else:
                raise RuntimeError(f"Failed to embed batch after {max_retries} retries.")

            # Upsert into ChromaDB
            self.collection.upsert(
                ids=ids,
                embeddings=embeddings,
                documents=texts,
                metadatas=metadatas,
            )

            added += len(batch)
            logger.info(f"  Progress: {added + skipped}/{total} chunks processed ({added} new, {skipped} skipped)")

            # Rate limit delay between batches (Gemini free tier)
            if i + batch_size < total:
                time.sleep(30)

        logger.info(f"✓ Successfully added {added} chunks to '{self.collection_name}'")
        return added

    def search(
        self,
        query: str,
        top_k: int = 5,
        filter_metadata: Optional[dict] = None,
    ) -> list[dict]:
        """
        Perform similarity search.

        Args:
            query: User query text.
            top_k: Number of results to return.
            filter_metadata: Optional ChromaDB where filter.

        Returns:
            List of result dicts with 'text', 'metadata', 'distance' keys.
        """
        # Embed the query
        query_embedding = self.embedding_fn.embed_query(query)

        # Build search kwargs
        search_kwargs = {
            "query_embeddings": [query_embedding],
            "n_results": top_k,
            "include": ["documents", "metadatas", "distances"],
        }
        if filter_metadata:
            search_kwargs["where"] = filter_metadata

        # Execute search
        results = self.collection.query(**search_kwargs)

        # Format results
        formatted = []
        if results and results["documents"]:
            for doc, meta, dist in zip(
                results["documents"][0],
                results["metadatas"][0],
                results["distances"][0],
            ):
                formatted.append({
                    "text": doc,
                    "metadata": meta,
                    "distance": dist,
                })

        return formatted

    def get_collection_stats(self) -> dict:
        """Get statistics about the current collection."""
        count = self.collection.count()
        return {
            "collection_name": self.collection_name,
            "total_documents": count,
            "persist_dir": self.persist_dir,
        }

    def reset_collection(self):
        """Delete and recreate the collection (for re-indexing)."""
        logger.warning(f"Resetting collection: {self.collection_name}")
        try:
            self.client.delete_collection(self.collection_name)
        except Exception:
            logger.info("Collection didn't exist, creating fresh.")
        self._collection = None
        # Recreate
        _ = self.collection
        logger.info("Collection reset complete.")

    @staticmethod
    def _sanitize_metadata(metadata: dict) -> dict:
        """
        Sanitize metadata for ChromaDB (only str, int, float, bool allowed).
        Removes None values and converts incompatible types.
        """
        sanitized = {}
        for key, value in metadata.items():
            if value is None:
                continue
            if isinstance(value, (str, int, float, bool)):
                sanitized[key] = value
            elif isinstance(value, (list, dict)):
                # Convert complex types to string
                sanitized[key] = str(value)
            else:
                sanitized[key] = str(value)
        return sanitized
