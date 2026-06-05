"""
Ingestion Pipeline: Raw JSON → Chunks → Embeddings → ChromaDB.
Run this to build/rebuild the vector index from scraped fund data.

Usage:
    python -m backend.ingestion.pipeline [--reset] [--provider gemini|huggingface]
"""

import argparse
import logging
import time

from backend.config import CHUNK_OVERLAP, CHUNK_SIZE, RAW_DATA_DIR
from backend.ingestion.chunker import chunk_all_funds, save_chunks
from backend.retrieval.vectorstore import VectorStore

# ──────────────────────────────────────────────
# Logging
# ──────────────────────────────────────────────
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger(__name__)


def run_pipeline(
    reset: bool = False,
    embedding_provider: str = None,
    chunk_size: int = CHUNK_SIZE,
    chunk_overlap: int = CHUNK_OVERLAP,
) -> dict:
    """
    Run the full ingestion pipeline: raw data → chunks → vector store.

    Args:
        reset: If True, delete existing collection before inserting.
        embedding_provider: "gemini" or "huggingface".
        chunk_size: Characters per chunk.
        chunk_overlap: Overlap between chunks.

    Returns:
        Summary dict with stats.
    """
    start_time = time.time()

    # ── Step 1: Chunk all fund data ──────────────────────
    logger.info("=" * 50)
    logger.info("STEP 1: Chunking raw fund data")
    logger.info("=" * 50)

    chunks = chunk_all_funds(
        data_dir=RAW_DATA_DIR,
        chunk_size=chunk_size,
        chunk_overlap=chunk_overlap,
    )

    if not chunks:
        logger.error("No chunks generated! Check data/raw/ for fund JSON files.")
        return {"error": "No chunks generated"}

    # Save chunks for debugging/inspection
    chunks_path = save_chunks(chunks)
    logger.info(f"Chunks saved to: {chunks_path}")

    # ── Step 2: Build vector store ───────────────────────
    logger.info("")
    logger.info("=" * 50)
    logger.info("STEP 2: Building vector store (embedding + indexing)")
    logger.info("=" * 50)

    store = VectorStore(embedding_provider=embedding_provider)

    if reset:
        logger.info("Resetting existing collection...")
        store.reset_collection()

    added = store.add_chunks(chunks, batch_size=10)

    # ── Summary ──────────────────────────────────────────
    elapsed = time.time() - start_time
    stats = store.get_collection_stats()

    summary = {
        "chunks_created": len(chunks),
        "chunks_added_to_store": added,
        "collection_total": stats["total_documents"],
        "collection_name": stats["collection_name"],
        "elapsed_seconds": round(elapsed, 1),
        "embedding_provider": embedding_provider or "default (config)",
    }

    logger.info("")
    logger.info("=" * 50)
    logger.info("PIPELINE COMPLETE")
    logger.info("=" * 50)
    for k, v in summary.items():
        logger.info(f"  {k}: {v}")

    return summary


# ──────────────────────────────────────────────
# CLI Entry Point
# ──────────────────────────────────────────────
if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Run the ingestion pipeline: raw JSON → chunks → vector store"
    )
    parser.add_argument(
        "--reset",
        action="store_true",
        help="Reset (delete + recreate) the vector store collection before inserting",
    )
    parser.add_argument(
        "--provider",
        type=str,
        choices=["gemini", "huggingface", "chroma_default"],
        default=None,
        help="Embedding provider (default: from config/env)",
    )
    parser.add_argument(
        "--chunk-size",
        type=int,
        default=CHUNK_SIZE,
        help=f"Chunk size in characters (default: {CHUNK_SIZE})",
    )
    parser.add_argument(
        "--chunk-overlap",
        type=int,
        default=CHUNK_OVERLAP,
        help=f"Chunk overlap in characters (default: {CHUNK_OVERLAP})",
    )
    args = parser.parse_args()

    summary = run_pipeline(
        reset=args.reset,
        embedding_provider=args.provider,
        chunk_size=args.chunk_size,
        chunk_overlap=args.chunk_overlap,
    )

    print(f"\n✅ Pipeline complete: {summary.get('chunks_added_to_store', 0)} chunks indexed")
    print(f"⏱  Time: {summary.get('elapsed_seconds', 0)}s")
