"""
Configuration module for the Mutual Fund FAQ Assistant.
Loads environment variables and provides application-wide settings.
"""

import os
from pathlib import Path
from dotenv import load_dotenv

# ──────────────────────────────────────────────
# Load .env file
# ──────────────────────────────────────────────
PROJECT_ROOT = Path(__file__).parent.parent
load_dotenv(PROJECT_ROOT / ".env")

# ──────────────────────────────────────────────
# LLM Provider Keys
# ──────────────────────────────────────────────
GROQ_API_KEY = os.getenv("GROQ_API_KEY", "")
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY", "")

# ──────────────────────────────────────────────
# LLM Settings
# ──────────────────────────────────────────────
LLM_PROVIDER = os.getenv("LLM_PROVIDER", "groq")  # "groq", "gemini", or "both"
GROQ_MODEL = os.getenv("GROQ_MODEL", "llama-3.3-70b-versatile")
GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-2.0-flash")

# ──────────────────────────────────────────────
# Embedding Settings
# ──────────────────────────────────────────────
EMBEDDING_PROVIDER = os.getenv("EMBEDDING_PROVIDER", "gemini")
GEMINI_EMBEDDING_MODEL = os.getenv("GEMINI_EMBEDDING_MODEL", "models/gemini-embedding-001")

# ──────────────────────────────────────────────
# Scraping Settings
# ──────────────────────────────────────────────
SCRAPE_DELAY_SECONDS = int(os.getenv("SCRAPE_DELAY_SECONDS", "2"))
USER_AGENT = os.getenv(
    "USER_AGENT",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
)

# ──────────────────────────────────────────────
# Data Paths
# ──────────────────────────────────────────────
DATA_DIR = PROJECT_ROOT / "data"
RAW_DATA_DIR = DATA_DIR / "raw"
PROCESSED_DATA_DIR = DATA_DIR / "processed"
VECTORDB_DIR = DATA_DIR / "vectordb"

# Ensure directories exist
RAW_DATA_DIR.mkdir(parents=True, exist_ok=True)
PROCESSED_DATA_DIR.mkdir(parents=True, exist_ok=True)
VECTORDB_DIR.mkdir(parents=True, exist_ok=True)

# ──────────────────────────────────────────────
# Vector Store Settings
# ──────────────────────────────────────────────
CHROMA_PERSIST_DIR = str(os.getenv("CHROMA_PERSIST_DIR", VECTORDB_DIR))
CHROMA_COLLECTION_NAME = os.getenv("CHROMA_COLLECTION_NAME", "mutual_fund_facts")

# ──────────────────────────────────────────────
# RAG Settings
# ──────────────────────────────────────────────
TOP_K = int(os.getenv("TOP_K", "5"))
CHUNK_SIZE = int(os.getenv("CHUNK_SIZE", "500"))
CHUNK_OVERLAP = int(os.getenv("CHUNK_OVERLAP", "100"))

# ──────────────────────────────────────────────
# Scheduler Settings
# ──────────────────────────────────────────────
SCHEDULER_HOUR = int(os.getenv("SCHEDULER_HOUR", "2"))
SCHEDULER_MINUTE = int(os.getenv("SCHEDULER_MINUTE", "0"))
SCHEDULER_TIMEZONE = os.getenv("SCHEDULER_TIMEZONE", "Asia/Kolkata")
