"""
PII Detector module.
Detects personally identifiable information in user queries:
PAN, Aadhaar, phone numbers, email addresses, and OTP-like patterns.
"""

import re
import logging
from typing import Dict, List, Tuple

logger = logging.getLogger(__name__)


# ──────────────────────────────────────────────
# PII Regex Patterns
# ──────────────────────────────────────────────

PII_PATTERNS: Dict[str, re.Pattern] = {
    "PAN": re.compile(r"\b[A-Z]{5}\d{4}[A-Z]\b"),
    "Aadhaar": re.compile(r"\b\d{4}[\s-]?\d{4}[\s-]?\d{4}\b"),
    "Phone": re.compile(r"\b(?:\+91[\s-]?)?[6-9]\d{9}\b"),
    "Email": re.compile(r"\b[\w.-]+@[\w.-]+\.\w{2,}\b"),
    "OTP": re.compile(r"\b(?:otp|OTP|pin|PIN)[\s:]*\d{4,6}\b"),
}

# Additional context patterns that hint at PII disclosure intent
PII_CONTEXT_PATTERNS: List[re.Pattern] = [
    re.compile(r"\bmy\s+(?:pan|aadhaar|aadhar|phone|mobile|email)\b", re.IGNORECASE),
    re.compile(r"\b(?:pan|aadhaar|aadhar)\s*(?:number|no|num|card)\s*(?:is|:)\b", re.IGNORECASE),
    re.compile(r"\b(?:account|demat|folio)\s*(?:number|no|num)\s*(?:is|:)\s*\w+", re.IGNORECASE),
]


# ──────────────────────────────────────────────
# PII Refusal Response
# ──────────────────────────────────────────────

PII_REFUSAL_RESPONSE = (
    "⚠️ I detected what appears to be personal/sensitive information in your message "
    "(such as PAN, Aadhaar, phone number, email, or OTP). "
    "For your security, I cannot process queries containing personal data.\n\n"
    "Please remove any personal information and rephrase your question. "
    "I can help with factual questions about mutual funds like NAV, expense ratio, "
    "exit load, fund managers, etc."
)


# ──────────────────────────────────────────────
# Detection Functions
# ──────────────────────────────────────────────

def detect_pii(text: str) -> List[Tuple[str, str]]:
    """
    Scan text for PII patterns.

    Args:
        text: User input text.

    Returns:
        List of (pii_type, matched_text) tuples.
        Empty list if no PII detected.
    """
    detections = []

    for pii_type, pattern in PII_PATTERNS.items():
        matches = pattern.findall(text)
        for match in matches:
            # Validate: avoid false positives
            if pii_type == "Aadhaar" and not _validate_aadhaar(match):
                continue
            if pii_type == "Phone" and not _validate_phone(match, text):
                continue
            detections.append((pii_type, match))

    # Check context patterns
    for pattern in PII_CONTEXT_PATTERNS:
        if pattern.search(text):
            detections.append(("PII_Context", pattern.pattern))
            break  # One context match is enough

    if detections:
        logger.warning(
            f"PII detected in query: {[d[0] for d in detections]} "
            f"(types only, values redacted for logging)"
        )

    return detections


def contains_pii(text: str) -> bool:
    """
    Quick boolean check: does the text contain PII?

    Args:
        text: User input text.

    Returns:
        True if PII is detected, False otherwise.
    """
    return len(detect_pii(text)) > 0


def get_pii_refusal() -> dict:
    """
    Get a standardized refusal response for PII-containing queries.

    Returns:
        Dict matching RAGChain.query() response format.
    """
    return {
        "answer": PII_REFUSAL_RESPONSE,
        "source_url": "",
        "fund_name": "",
        "last_updated": "",
        "chunks_used": 0,
        "blocked_by": "pii_detector",
    }


# ──────────────────────────────────────────────
# Validation Helpers (reduce false positives)
# ──────────────────────────────────────────────

def _validate_aadhaar(match: str) -> bool:
    """
    Validate Aadhaar-like match: must be exactly 12 digits
    and not look like a financial amount or date.
    """
    digits = re.sub(r"[\s-]", "", match)
    if len(digits) != 12:
        return False
    # Aadhaar numbers don't start with 0 or 1
    if digits[0] in ("0", "1"):
        return False
    return True


def _validate_phone(match: str, full_text: str) -> bool:
    """
    Validate phone number: avoid matching NAV values, AUM numbers,
    or other financial figures that happen to be 10 digits.
    """
    # Remove +91 prefix if present
    clean = re.sub(r"^\+91[\s-]?", "", match)
    if len(clean) != 10:
        return False

    # Check if this number is preceded by ₹, Rs, INR, or financial context
    # which would indicate it's a monetary value, not a phone number
    financial_prefix = re.compile(
        r"(?:₹|Rs\.?|INR|AUM|NAV|crore|lakh)\s*" + re.escape(clean),
        re.IGNORECASE,
    )
    if financial_prefix.search(full_text):
        return False

    return True
