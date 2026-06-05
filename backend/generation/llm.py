"""
LLM wrapper module.
Supports Groq (llama-3.3-70b-versatile) and Gemini (gemini-2.0-flash) with failover.
"""

import logging
from typing import Optional

from backend.config import (
    LLM_PROVIDER,
    GROQ_API_KEY,
    GROQ_MODEL,
    GOOGLE_API_KEY,
    GEMINI_MODEL,
)

logger = logging.getLogger(__name__)


class LLMManager:
    """
    Manages LLM instances with provider switching and failover.
    Supports: groq, gemini, both (groq primary + gemini fallback).
    """

    def __init__(self, provider: Optional[str] = None):
        """
        Initialize LLM manager.

        Args:
            provider: "groq", "gemini", or "both". Defaults to config.
        """
        self.provider = provider or LLM_PROVIDER
        self._llm = None
        self._fallback_llm = None

    @property
    def llm(self):
        """Lazy-load the primary LLM."""
        if self._llm is None:
            self._llm = self._create_llm(self._primary_provider)
        return self._llm

    @property
    def _primary_provider(self) -> str:
        """Determine primary provider."""
        if self.provider == "both":
            return "groq"
        return self.provider

    @property
    def _fallback_provider(self) -> Optional[str]:
        """Determine fallback provider."""
        if self.provider == "both":
            return "gemini"
        return None

    def _create_llm(self, provider: str):
        """Create an LLM instance for the given provider."""
        if provider == "groq":
            return self._create_groq_llm()
        elif provider == "gemini":
            return self._create_gemini_llm()
        else:
            raise ValueError(f"Unknown LLM provider: {provider}")

    def _create_groq_llm(self):
        """Create Groq LLM (llama-3.3-70b-versatile)."""
        from langchain_groq import ChatGroq

        if not GROQ_API_KEY:
            raise ValueError("GROQ_API_KEY not set. Add it to your .env file.")

        logger.info(f"Initializing Groq LLM: {GROQ_MODEL}")
        return ChatGroq(
            model=GROQ_MODEL,
            api_key=GROQ_API_KEY,
            temperature=0,
            max_tokens=512,
        )

    def _create_gemini_llm(self):
        """Create Gemini LLM (gemini-2.0-flash)."""
        from langchain_google_genai import ChatGoogleGenerativeAI

        if not GOOGLE_API_KEY:
            raise ValueError("GOOGLE_API_KEY not set. Add it to your .env file.")

        logger.info(f"Initializing Gemini LLM: {GEMINI_MODEL}")
        return ChatGoogleGenerativeAI(
            model=GEMINI_MODEL,
            google_api_key=GOOGLE_API_KEY,
            temperature=0,
            max_output_tokens=512,
        )

    def generate(self, messages: list[dict]) -> str:
        """
        Generate a response from the LLM.

        Args:
            messages: List of message dicts with 'role' and 'content' keys.
                     Roles: "system", "human", "ai"

        Returns:
            Generated text response.

        Raises:
            Exception if both primary and fallback fail.
        """
        from langchain_core.messages import SystemMessage, HumanMessage, AIMessage

        # Convert to LangChain message objects
        lc_messages = []
        for msg in messages:
            role = msg["role"]
            content = msg["content"]
            if role == "system":
                lc_messages.append(SystemMessage(content=content))
            elif role == "human":
                lc_messages.append(HumanMessage(content=content))
            elif role == "ai":
                lc_messages.append(AIMessage(content=content))

        # Try primary LLM
        try:
            response = self.llm.invoke(lc_messages)
            return response.content
        except Exception as e:
            logger.error(f"Primary LLM ({self._primary_provider}) failed: {e}")

            # Try fallback if configured
            if self._fallback_provider:
                logger.info(f"Falling back to {self._fallback_provider}...")
                try:
                    if self._fallback_llm is None:
                        self._fallback_llm = self._create_llm(self._fallback_provider)
                    response = self._fallback_llm.invoke(lc_messages)
                    return response.content
                except Exception as fallback_error:
                    logger.error(f"Fallback LLM failed: {fallback_error}")
                    raise RuntimeError(
                        f"Both LLMs failed. Primary: {e}, Fallback: {fallback_error}"
                    )
            raise


def get_llm(provider: Optional[str] = None) -> LLMManager:
    """
    Factory function to get an LLM manager instance.

    Args:
        provider: "groq", "gemini", or "both".

    Returns:
        LLMManager instance.
    """
    return LLMManager(provider)
