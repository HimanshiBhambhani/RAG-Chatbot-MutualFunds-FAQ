"""
FastAPI server for the Mutual Fund FAQ Assistant.
Exposes /api/chat endpoint for the Next.js frontend.
"""

import os
import sys
import logging
from pathlib import Path
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

# Ensure project root is in path
sys.path.insert(0, str(Path(__file__).parent.parent))

from backend.generation.chain import RAGChain
from backend.ingestion.fund_urls import FUND_URLS

logger = logging.getLogger(__name__)

# ──────────────────────────────────────────────
# Global chain instance (loaded once at startup)
# ──────────────────────────────────────────────
rag_chain: RAGChain = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Initialize RAG chain on startup."""
    global rag_chain
    logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
    logger.info("Initializing RAG Chain...")
    rag_chain = RAGChain()
    logger.info("RAG Chain ready.")
    yield
    logger.info("Shutting down.")


app = FastAPI(
    title="Mutual Fund FAQ Assistant API",
    version="1.0.0",
    lifespan=lifespan,
)

# CORS — allow all origins (public read-only API)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ──────────────────────────────────────────────
# Request / Response Models
# ──────────────────────────────────────────────

class ChatRequest(BaseModel):
    query: str


class ChatResponse(BaseModel):
    answer: str
    source_url: str
    fund_name: str
    last_updated: str
    chunks_used: int
    blocked_by: str = ""


class CategoryFund(BaseModel):
    name: str
    slug: str


class Category(BaseModel):
    category: str
    icon: str
    subtitle: str
    funds: list[CategoryFund]


# ──────────────────────────────────────────────
# Category metadata for sidebar
# ──────────────────────────────────────────────

CATEGORY_META = {
    "Large Cap": {"icon": "📈", "subtitle": "Stability & steady growth"},
    "Mid Cap": {"icon": "📊", "subtitle": "Balanced risk-reward"},
    "Small Cap": {"icon": "🚀", "subtitle": "High potential volatility"},
    "Flexi Cap / Focused": {"icon": "🎯", "subtitle": "Diversified allocation"},
    "Defence": {"icon": "🛡️", "subtitle": "Sector specific focus"},
    "Equity / Thematic": {"icon": "🏛️", "subtitle": "Pure stock-based funds"},
}


# ──────────────────────────────────────────────
# Endpoints
# ──────────────────────────────────────────────

@app.post("/api/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    """Process a chat query through the RAG pipeline with guardrails."""
    if not request.query.strip():
        raise HTTPException(status_code=400, detail="Query cannot be empty")

    try:
        result = rag_chain.query(request.query.strip())
        return ChatResponse(
            answer=result["answer"],
            source_url=result.get("source_url", ""),
            fund_name=result.get("fund_name", ""),
            last_updated=result.get("last_updated", ""),
            chunks_used=result.get("chunks_used", 0),
            blocked_by=result.get("blocked_by", ""),
        )
    except Exception as e:
        logger.error(f"Error processing query: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@app.get("/api/categories", response_model=list[Category])
async def get_categories():
    """Return fund categories with their funds for the sidebar."""
    categories = []
    for cat_name, funds in FUND_URLS.items():
        meta = CATEGORY_META.get(cat_name, {"icon": "📁", "subtitle": ""})
        categories.append(Category(
            category=cat_name,
            icon=meta["icon"],
            subtitle=meta["subtitle"],
            funds=[CategoryFund(name=f["name"], slug=f["slug"]) for f in funds],
        ))
    return categories


@app.get("/api/health")
async def health():
    """Health check endpoint."""
    return {"status": "ok", "chain_loaded": rag_chain is not None}


# ──────────────────────────────────────────────
# Run with: uvicorn backend.api:app --reload --port 8000
# ──────────────────────────────────────────────
