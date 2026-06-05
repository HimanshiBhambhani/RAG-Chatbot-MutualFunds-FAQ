"""
Refusal module.
Classifies advisory/investment-advice queries and provides polite refusal responses.
Also handles off-topic queries unrelated to mutual funds.
"""

import re
import logging
from typing import Optional

logger = logging.getLogger(__name__)


# ──────────────────────────────────────────────
# Advisory Keyword Patterns
# ──────────────────────────────────────────────

ADVISORY_PATTERNS: list[re.Pattern] = [
    # Direct advice-seeking
    re.compile(r"\bshould\s+i\s+(?:invest|buy|sell|redeem|switch)\b", re.IGNORECASE),
    re.compile(r"\bwhich\s+(?:fund|scheme|mutual fund)\s+(?:is|are)\s+(?:better|best|good)\b", re.IGNORECASE),
    re.compile(r"\brecommend\b", re.IGNORECASE),
    re.compile(r"\bsugg(?:est|estion)\b", re.IGNORECASE),
    re.compile(r"\bbest\s+(?:fund|scheme|mutual fund)\s+(?:to|for)\b", re.IGNORECASE),
    re.compile(r"\b(?:will|can)\s+(?:it|this|the fund|this fund)\s+(?:\w+\s+)?(?:give|provide|generate)\s+(?:good\s+)?returns\b", re.IGNORECASE),
    re.compile(r"\bcompare\s+(?:performance|returns)\b", re.IGNORECASE),
    re.compile(r"\bbuy\s+or\s+sell\b", re.IGNORECASE),
    re.compile(r"\bgood\s+investment\b", re.IGNORECASE),
    re.compile(r"\bfuture\s+(?:prediction|forecast|outlook|return)\b", re.IGNORECASE),
    re.compile(r"\b(?:safe|risky)\s+(?:to\s+)?invest\b", re.IGNORECASE),
    re.compile(r"\bhow\s+much\s+(?:should|can)\s+i\s+invest\b", re.IGNORECASE),
    re.compile(r"\b(?:worth|worthwhile)\s+(?:investing|buying)\b", re.IGNORECASE),
    re.compile(r"\bwill\s+(?:it|this)\s+(?:\w+\s+)?(?:grow|increase|double|triple)\b", re.IGNORECASE),
    re.compile(r"\b(?:better|worse)\s+than\s+(?:fd|fixed deposit|ppf|gold|stock)\b", re.IGNORECASE),
    re.compile(r"\btip(?:s)?\s+(?:for|on)\s+(?:investing|mutual fund)\b", re.IGNORECASE),
    re.compile(r"\bwhat\s+(?:should|do)\s+(?:i|you)\s+(?:invest|do)\b", re.IGNORECASE),
    re.compile(r"\bpredict\b", re.IGNORECASE),
    re.compile(r"\bguarantee[sd]?\s+returns?\b", re.IGNORECASE),
    re.compile(r"\brisk-free\b", re.IGNORECASE),
]

# Off-topic patterns (not mutual fund related at all)
OFF_TOPIC_PATTERNS: list[re.Pattern] = [
    re.compile(r"\b(?:weather|cricket|movie|recipe|joke|song|poem)\b", re.IGNORECASE),
    re.compile(r"\b(?:who\s+is\s+the\s+(?:president|prime minister|pm))\b", re.IGNORECASE),
    re.compile(r"\b(?:write|generate|create)\s+(?:a\s+)?(?:code|program|essay|story)\b", re.IGNORECASE),
    re.compile(r"\b(?:hello+|hii*|hey+|howdy|what's up|how are you)\b(?:\s+\w+)?\s*[?!.]?\s*$", re.IGNORECASE),
]


# ──────────────────────────────────────────────
# Refusal Response Templates
# ──────────────────────────────────────────────

ADVISORY_REFUSAL_RESPONSE = (
    "I'm a facts-only assistant and cannot provide investment advice, "
    "recommendations, or predictions.\n\n"
    "I can help you with factual information like:\n"
    "• NAV, expense ratio, exit load\n"
    "• Fund managers and holdings\n"
    "• AUM, benchmark, risk category\n\n"
    "For investment advice, please consult a SEBI-registered investment advisor.\n"
    "🔗 AMFI India: https://www.amfiindia.com/\n"
    "🔗 SEBI: https://www.sebi.gov.in/"
)

OFF_TOPIC_REFUSAL_RESPONSE = (
    "I can only answer factual questions about mutual funds listed on Groww. "
    "Try asking about NAV, expense ratio, fund managers, exit load, AUM, "
    "or other fund details.\n\n"
    "For general queries, please use a general-purpose assistant."
)

GREETING_RESPONSE = (
    "Hello! I'm a mutual fund FAQ assistant. I can answer factual questions about "
    "60 mutual funds listed on Groww.\n\n"
    "Try asking:\n"
    "• What is the expense ratio of HDFC Defence Fund?\n"
    "• Who manages the SBI Small Cap Fund?\n"
    "• What is the exit load for Axis Midcap Fund?\n\n"
    "⚠️ I provide facts only — no investment advice."
)


# ──────────────────────────────────────────────
# Classification Functions
# ──────────────────────────────────────────────

def classify_query(text: str) -> Optional[str]:
    """
    Classify the query intent for refusal purposes.

    Args:
        text: User input text.

    Returns:
        - "advisory" if the query seeks investment advice
        - "off_topic" if the query is unrelated to mutual funds
        - "greeting" if it's a simple greeting
        - None if the query is valid (should proceed to RAG)
    """
    text_stripped = text.strip()

    # Check for greetings first (short messages)
    if len(text_stripped.split()) <= 4:
        for pattern in OFF_TOPIC_PATTERNS:
            if pattern.search(text_stripped):
                # Distinguish greeting from off-topic
                if re.match(r"^(?:hello+|hii*|hey+|howdy|what'?s up|how are you)", text_stripped, re.IGNORECASE):
                    return "greeting"
                return "off_topic"

    # Check advisory patterns
    for pattern in ADVISORY_PATTERNS:
        if pattern.search(text):
            logger.info(f"Advisory query detected: matched pattern '{pattern.pattern}'")
            return "advisory"

    # Check off-topic patterns (only for longer messages)
    for pattern in OFF_TOPIC_PATTERNS:
        if pattern.search(text):
            # But don't flag if it also contains fund-related keywords
            fund_keywords = re.compile(
                r"\b(?:fund|mutual|nav|expense|sip|lumpsum|aum|nfo|groww|"
                r"hdfc|sbi|icici|axis|nippon|motilal|kotak|tata|dsp|mirae)\b",
                re.IGNORECASE,
            )
            if not fund_keywords.search(text):
                logger.info(f"Off-topic query detected: '{text[:50]}...'")
                return "off_topic"

    return None


def is_advisory_query(text: str) -> bool:
    """
    Quick boolean check: does the query seek investment advice?

    Args:
        text: User input text.

    Returns:
        True if the query is advisory in nature.
    """
    return classify_query(text) == "advisory"


def get_refusal_response(classification: str) -> dict:
    """
    Get a standardized refusal response based on query classification.

    Args:
        classification: One of "advisory", "off_topic", "greeting".

    Returns:
        Dict matching RAGChain.query() response format.
    """
    responses = {
        "advisory": ADVISORY_REFUSAL_RESPONSE,
        "off_topic": OFF_TOPIC_REFUSAL_RESPONSE,
        "greeting": GREETING_RESPONSE,
    }

    answer = responses.get(classification, OFF_TOPIC_REFUSAL_RESPONSE)

    return {
        "answer": answer,
        "source_url": "",
        "fund_name": "",
        "last_updated": "",
        "chunks_used": 0,
        "blocked_by": f"refusal_{classification}",
    }
