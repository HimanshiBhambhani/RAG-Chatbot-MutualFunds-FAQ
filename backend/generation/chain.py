"""
RAG Chain module.
Orchestrates the full pipeline: query → guardrails → retrieve → generate → validate.
"""

import logging
from datetime import datetime
from typing import Optional

from backend.retrieval.retriever import Retriever
from backend.generation.llm import LLMManager, get_llm
from backend.generation.prompts import (
    SYSTEM_PROMPT,
    USER_PROMPT_TEMPLATE,
    NO_CONTEXT_RESPONSE,
)
from backend.guardrails.pii_detector import contains_pii, get_pii_refusal
from backend.guardrails.refusal import classify_query, get_refusal_response
from backend.guardrails.validator import validate_response, sanitize_response

logger = logging.getLogger(__name__)


class RAGChain:
    """
    End-to-end RAG chain: retrieval + generation with citation.
    """

    def __init__(
        self,
        llm_provider: Optional[str] = None,
        embedding_provider: Optional[str] = None,
        top_k: int = 5,
        use_rerank: bool = True,
    ):
        """
        Initialize the RAG chain.

        Args:
            llm_provider: "groq", "gemini", or "both".
            embedding_provider: "gemini", "huggingface", or "chroma_default".
            top_k: Number of chunks to retrieve.
            use_rerank: Whether to apply metadata-based re-ranking.
        """
        self.retriever = Retriever(
            top_k=top_k,
            embedding_provider=embedding_provider,
        )
        self.llm = get_llm(llm_provider)
        self.use_rerank = use_rerank
        self.top_k = top_k

        logger.info(
            f"RAG Chain initialized (LLM={self.llm.provider}, "
            f"top_k={top_k}, rerank={use_rerank})"
        )

    def query(self, question: str, history: list[dict] = None) -> dict:
        """
        Process a user question through the full RAG pipeline with guardrails.

        Args:
            question: User's natural language question.
            history: Optional list of prior messages [{"role": "user"|"bot", "content": "..."}]

        Returns:
            Dict with keys:
                - answer: Generated response text
                - source_url: Citation URL from top chunk
                - fund_name: Name of the fund referenced
                - last_updated: Date of last data scrape
                - chunks_used: Number of chunks used for context
                - blocked_by: (optional) Guardrail that blocked the query
        """
        if history is None:
            history = []
        # ── Pre-query Guardrail 1: PII Detection ──
        if contains_pii(question):
            logger.warning("Query blocked by PII detector")
            return get_pii_refusal()

        # ── Pre-query Guardrail 2: Advisory/Off-topic Refusal ──
        classification = classify_query(question)
        if classification is not None:
            logger.info(f"Query classified as '{classification}' — refusing")
            return get_refusal_response(classification)

        # Step 1: Retrieve relevant chunks
        if self.use_rerank:
            results = self.retriever.retrieve_with_rerank(question, top_k=self.top_k)
        else:
            results = self.retriever.retrieve(question, top_k=self.top_k)

        # Step 2: Handle no results
        if not results:
            return {
                "answer": NO_CONTEXT_RESPONSE,
                "source_url": "",
                "fund_name": "",
                "last_updated": "",
                "chunks_used": 0,
            }

        # Step 3: Format context from retrieved chunks
        context = self.retriever.format_context(results)
        top_source = self.retriever.get_top_source(results)

        # Step 4: Determine last_updated date
        scraped_at = top_source.get("scraped_at", "")
        if scraped_at:
            try:
                dt = datetime.fromisoformat(scraped_at.replace("Z", "+00:00"))
                last_updated = dt.strftime("%d %B %Y")
            except (ValueError, TypeError):
                last_updated = scraped_at[:10] if len(scraped_at) >= 10 else "Unknown"
        else:
            last_updated = "Unknown"

        # Step 5: Build messages for LLM (with conversation history)
        system_prompt = SYSTEM_PROMPT.format(last_updated=last_updated)
        user_prompt = USER_PROMPT_TEMPLATE.format(
            context=context,
            question=question,
        )

        messages = [
            {"role": "system", "content": system_prompt},
        ]

        # Inject conversation history (last 10 exchanges max to stay within token limits)
        for msg in history[-20:]:
            role = "human" if msg["role"] == "user" else "ai"
            messages.append({"role": role, "content": msg["content"]})

        # Current user query with retrieved context
        messages.append({"role": "human", "content": user_prompt})

        # Step 6: Generate response
        try:
            answer = self.llm.generate(messages)
        except Exception as e:
            logger.error(f"LLM generation failed: {e}")
            answer = (
                "I'm experiencing a technical issue and cannot generate a response "
                "right now. Please try again in a moment."
            )

        # Step 7: Ensure citation is present (append if LLM didn't include it)
        source_url = top_source.get("source_url", "")
        if source_url and source_url not in answer:
            if not answer.strip().endswith(source_url):
                # Don't double-add if LLM already included a Source line
                if "Source:" not in answer and "source:" not in answer.lower():
                    answer = f"{answer}\n\nSource: {source_url}"

        # Step 8: Ensure last_updated footer
        footer = f"Last updated from sources: {last_updated}"
        if footer not in answer and "Last updated" not in answer:
            answer = f"{answer}\n{footer}"

        # ── Post-response Guardrail: Validate response ──
        validation = validate_response(
            response=answer,
            source_url=source_url,
            original_query=question,
        )
        if not validation.is_valid:
            logger.warning(f"Response failed validation: {validation.issues}")
            answer = sanitize_response(answer, validation)

        return {
            "answer": answer,
            "source_url": source_url,
            "fund_name": self._get_relevant_fund_name(question, top_source),
            "last_updated": last_updated,
            "chunks_used": len(results),
        }

    def _get_relevant_fund_name(self, question: str, top_source: dict) -> str:
        """
        Only return fund_name if the user's query is actually about a specific fund.
        Prevents showing a fund card for generic questions like "what is growth?"
        that happen to match a fund name in the vector store.
        """
        fund_name = top_source.get("fund_name", "")
        if not fund_name:
            return ""

        question_lower = question.lower()

        # Check if the query mentions a recognizable part of the fund name
        # e.g., "HDFC Defence" in "HDFC Defence Fund Direct Growth"
        fund_words = fund_name.lower().replace("direct growth", "").replace("direct plan growth", "").strip()
        fund_parts = fund_words.split()

        # Look for AMC name (first word: HDFC, SBI, ICICI, Nippon, etc.)
        amc_names = [
            "hdfc", "sbi", "icici", "axis", "nippon", "motilal", "kotak",
            "tata", "dsp", "mirae", "parag", "quant", "uti", "navi",
            "edelweiss", "invesco", "whiteoak", "hsbc", "bandhan",
            "canara", "franklin", "aditya", "jioblackrock", "bank of india",
        ]

        # If query mentions an AMC name that matches the fund's AMC
        for amc in amc_names:
            if amc in question_lower and amc in fund_name.lower():
                return fund_name

        # If query mentions a meaningful fund keyword (not just "growth", "fund", "direct")
        generic_words = {"fund", "growth", "direct", "plan", "index", "cap", "the", "what", "is", "of", "for", "a", "an"}
        meaningful_fund_words = [w for w in fund_parts if w.lower() not in generic_words and len(w) > 2]

        for word in meaningful_fund_words:
            if word in question_lower:
                return fund_name

        # If query explicitly mentions "tell me about" pattern (from sidebar click)
        if "tell me about" in question_lower:
            return fund_name

        # Generic query — don't attribute to a specific fund
        return ""


# ──────────────────────────────────────────────
# CLI interface for terminal testing
# ──────────────────────────────────────────────

def main():
    """Interactive terminal Q&A for testing the RAG chain."""
    import sys

    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(message)s",
        datefmt="%H:%M:%S",
    )

    print("=" * 60)
    print("  Mutual Fund FAQ Assistant (RAG Pipeline)")
    print("  Type your question or 'quit' to exit.")
    print("=" * 60)
    print()

    chain = RAGChain()

    while True:
        try:
            question = input("\n💬 You: ").strip()
        except (KeyboardInterrupt, EOFError):
            print("\n\nGoodbye!")
            break

        if not question:
            continue
        if question.lower() in ("quit", "exit", "q"):
            print("\nGoodbye!")
            break

        print("\n🔍 Searching...")
        result = chain.query(question)

        print(f"\n🤖 Assistant:\n{result['answer']}")
        print(f"\n   [Chunks used: {result['chunks_used']}]")


if __name__ == "__main__":
    main()
