"""
Text Chunker for mutual fund data.
Splits fund text into overlapping chunks with metadata for RAG retrieval.
"""

import json
import logging
from pathlib import Path
from typing import Optional

from langchain_text_splitters import RecursiveCharacterTextSplitter

from backend.config import CHUNK_OVERLAP, CHUNK_SIZE, RAW_DATA_DIR

logger = logging.getLogger(__name__)


def create_text_splitter(
    chunk_size: int = CHUNK_SIZE,
    chunk_overlap: int = CHUNK_OVERLAP,
) -> RecursiveCharacterTextSplitter:
    """
    Create a configured text splitter.

    Args:
        chunk_size: Max characters per chunk.
        chunk_overlap: Overlapping characters between consecutive chunks.

    Returns:
        Configured RecursiveCharacterTextSplitter instance.
    """
    return RecursiveCharacterTextSplitter(
        chunk_size=chunk_size,
        chunk_overlap=chunk_overlap,
        separators=["\n\n", "\n", ". ", ", ", " "],
        length_function=len,
        is_separator_regex=False,
    )


def chunk_fund_data(fund_data: dict, splitter: Optional[RecursiveCharacterTextSplitter] = None) -> list[dict]:
    """
    Split a single fund's data into chunks with metadata.

    Each chunk gets metadata including fund name, category, URL, etc.
    for filtering during retrieval.

    Args:
        fund_data: Parsed fund JSON dict (from data/raw/).
        splitter: Text splitter instance (creates default if None).

    Returns:
        List of chunk dicts with 'text' and 'metadata' keys.
    """
    if splitter is None:
        splitter = create_text_splitter()

    full_text = fund_data.get("full_text", "")
    if not full_text:
        logger.warning(f"No full_text for fund: {fund_data.get('fund_name', 'Unknown')}")
        return []

    # Split text into chunks
    text_chunks = splitter.split_text(full_text)

    # Build metadata common to all chunks of this fund
    base_metadata = {
        "fund_name": fund_data.get("fund_name") or fund_data.get("scheme_name", "Unknown"),
        "scheme_name": fund_data.get("scheme_name", ""),
        "fund_house": fund_data.get("fund_house", ""),
        "category": fund_data.get("category", ""),
        "sub_category": fund_data.get("sub_category", ""),
        "risk_level": fund_data.get("risk_level", ""),
        "source_url": fund_data.get("source_url", ""),
        "slug": fund_data.get("slug", ""),
        "isin": fund_data.get("isin", ""),
        "nav": fund_data.get("nav"),
        "scraped_at": fund_data.get("scraped_at", ""),
    }

    # Create chunk documents with metadata
    chunks = []
    for i, text in enumerate(text_chunks):
        chunk = {
            "text": text,
            "metadata": {
                **base_metadata,
                "chunk_index": i,
                "total_chunks": len(text_chunks),
            },
        }
        chunks.append(chunk)

    return chunks


def chunk_all_funds(
    data_dir: Path = RAW_DATA_DIR,
    chunk_size: int = CHUNK_SIZE,
    chunk_overlap: int = CHUNK_OVERLAP,
) -> list[dict]:
    """
    Load all raw fund JSONs and chunk them.

    Args:
        data_dir: Directory containing raw fund JSON files.
        chunk_size: Max characters per chunk.
        chunk_overlap: Overlap between chunks.

    Returns:
        List of all chunk dicts across all funds.
    """
    splitter = create_text_splitter(chunk_size, chunk_overlap)

    json_files = sorted(data_dir.glob("*.json"))
    json_files = [f for f in json_files if not f.name.startswith("_")]

    logger.info(f"Chunking {len(json_files)} fund files from {data_dir}")

    all_chunks = []
    for filepath in json_files:
        with open(filepath, "r", encoding="utf-8") as f:
            fund_data = json.load(f)

        chunks = chunk_fund_data(fund_data, splitter)
        all_chunks.extend(chunks)

        logger.debug(f"  {filepath.stem}: {len(chunks)} chunks")

    logger.info(f"Total chunks created: {len(all_chunks)}")
    return all_chunks


def save_chunks(chunks: list[dict], output_path: Optional[Path] = None) -> Path:
    """
    Save chunks to a JSON file for inspection/debugging.

    Args:
        chunks: List of chunk dicts.
        output_path: Where to save. Defaults to data/processed/chunks.json.

    Returns:
        Path to saved file.
    """
    from backend.config import PROCESSED_DATA_DIR

    if output_path is None:
        output_path = PROCESSED_DATA_DIR / "chunks.json"

    output_path.parent.mkdir(parents=True, exist_ok=True)

    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(chunks, f, indent=2, ensure_ascii=False)

    logger.info(f"Saved {len(chunks)} chunks to {output_path}")
    return output_path
