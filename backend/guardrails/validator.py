"""
Response Validator module.
Validates LLM-generated responses for quality, safety, and compliance.
Checks: response length, citation presence, hallucination indicators, and advisory language.
"""

import re
import logging
from typing import Dict, List, Optional

logger = logging.getLogger(__name__)


# ──────────────────────────────────────────────
# Validation Configuration
# ──────────────────────────────────────────────

MAX_RESPONSE_SENTENCES = 5  # Allow slight buffer over the 3-sentence rule
MAX_RESPONSE_CHARS = 1500  # Safety cap
MIN_RESPONSE_CHARS = 10  # Too short = likely error

# Patterns that suggest the LLM is giving advice despite instructions
ADVISORY_LEAKAGE_PATTERNS: list[re.Pattern] = [
    re.compile(r"\bi\s+(?:recommend|suggest|advise)\b", re.IGNORECASE),
    re.compile(r"\byou\s+should\s+(?:invest|buy|sell)\b", re.IGNORECASE),
    re.compile(r"\bthis\s+is\s+a\s+good\s+(?:investment|choice|option)\b", re.IGNORECASE),
    re.compile(r"\bconsider\s+(?:investing|buying)\b", re.IGNORECASE),
    re.compile(r"\bguaranteed\s+returns\b", re.IGNORECASE),
    re.compile(r"\bwill\s+(?:definitely|surely|certainly)\s+(?:grow|increase)\b", re.IGNORECASE),
]

# Hallucination indicators (claims not typically in our data)
HALLUCINATION_INDICATORS: list[re.Pattern] = [
    re.compile(r"\bas\s+of\s+(?:today|now|currently|this moment)\b", re.IGNORECASE),
    re.compile(r"\baccording\s+to\s+(?:recent|latest)\s+(?:news|reports)\b", re.IGNORECASE),
    re.compile(r"\bin\s+my\s+(?:opinion|experience)\b", re.IGNORECASE),
]


# ──────────────────────────────────────────────
# Validation Result
# ──────────────────────────────────────────────

class ValidationResult:
    """Result of response validation."""

    def __init__(self):
        self.is_valid: bool = True
        self.issues: List[str] = []
        self.warnings: List[str] = []
        self.corrected_response: Optional[str] = None

    def add_issue(self, issue: str):
        """Add a blocking issue (response should be replaced)."""
        self.is_valid = False
        self.issues.append(issue)

    def add_warning(self, warning: str):
        """Add a non-blocking warning (response can still be used)."""
        self.warnings.append(warning)

    def __repr__(self):
        status = "VALID" if self.is_valid else "INVALID"
        return f"ValidationResult({status}, issues={self.issues}, warnings={self.warnings})"


# ──────────────────────────────────────────────
# Validation Functions
# ──────────────────────────────────────────────

def validate_response(
    response: str,
    source_url: str = "",
    original_query: str = "",
) -> ValidationResult:
    """
    Validate a generated response against quality and safety rules.

    Args:
        response: The LLM-generated response text.
        source_url: Expected source URL that should appear in response.
        original_query: The original user query (for context).

    Returns:
        ValidationResult with is_valid flag, issues, and warnings.
    """
    result = ValidationResult()

    # ── Check 1: Response length ──
    if len(response.strip()) < MIN_RESPONSE_CHARS:
        result.add_issue("Response is too short (likely an error)")
        return result

    if len(response) > MAX_RESPONSE_CHARS:
        result.add_warning(f"Response exceeds {MAX_RESPONSE_CHARS} chars ({len(response)})")

    # ── Check 2: Sentence count ──
    # Count sentences (rough: split by period, exclamation, question mark)
    # Exclude the Source: and Last updated lines
    response_body = _extract_body(response)
    sentences = _count_sentences(response_body)
    if sentences > MAX_RESPONSE_SENTENCES:
        result.add_warning(f"Response has {sentences} sentences (max recommended: 3)")

    # ── Check 3: Citation presence ──
    has_citation = bool(
        re.search(r"(?:Source|source|Reference|Ref):\s*https?://", response)
        or re.search(r"https?://groww\.in/", response)
    )
    if not has_citation and source_url:
        result.add_warning("Response missing source citation URL")

    # ── Check 4: Advisory language leakage ──
    for pattern in ADVISORY_LEAKAGE_PATTERNS:
        if pattern.search(response):
            result.add_issue(
                f"Response contains advisory language: '{pattern.pattern}'"
            )
            break

    # ── Check 5: Hallucination indicators ──
    for pattern in HALLUCINATION_INDICATORS:
        if pattern.search(response):
            result.add_warning(
                f"Possible hallucination indicator: '{pattern.pattern}'"
            )
            break

    # ── Check 6: PII in response (shouldn't echo back PII) ──
    from backend.guardrails.pii_detector import detect_pii
    pii_in_response = detect_pii(response)
    if pii_in_response:
        result.add_issue(
            f"Response contains PII: {[p[0] for p in pii_in_response]}"
        )

    if result.issues:
        logger.warning(f"Response validation FAILED: {result.issues}")
    elif result.warnings:
        logger.info(f"Response validation passed with warnings: {result.warnings}")

    return result


def sanitize_response(response: str, validation: ValidationResult) -> str:
    """
    Sanitize a response that failed validation.

    If the response has blocking issues, returns a safe fallback.
    If it only has warnings, returns the original response.

    Args:
        response: Original response text.
        validation: ValidationResult from validate_response().

    Returns:
        Safe response string.
    """
    if validation.is_valid:
        return response

    # If advisory language leaked through
    if any("advisory" in issue.lower() for issue in validation.issues):
        return (
            "I can only provide factual information about mutual funds. "
            "I cannot offer investment advice or recommendations.\n\n"
            "For investment guidance, please consult a SEBI-registered advisor.\n"
            "🔗 AMFI India: https://www.amfiindia.com/"
        )

    # If PII was echoed back
    if any("pii" in issue.lower() for issue in validation.issues):
        return (
            "I cannot include personal information in my responses. "
            "Please ask a factual question about mutual funds."
        )

    # Generic fallback
    return (
        "I wasn't able to generate a reliable response for this query. "
        "Please try rephrasing your question about mutual fund facts "
        "(NAV, expense ratio, fund manager, exit load, etc.)."
    )


# ──────────────────────────────────────────────
# Helper Functions
# ──────────────────────────────────────────────

def _extract_body(response: str) -> str:
    """Extract the main body of response, excluding Source/Last updated lines."""
    lines = response.strip().split("\n")
    body_lines = []
    for line in lines:
        if line.strip().startswith(("Source:", "Last updated", "🔗")):
            continue
        body_lines.append(line)
    return " ".join(body_lines)


def _count_sentences(text: str) -> int:
    """Count approximate number of sentences in text."""
    # Split on sentence-ending punctuation
    sentences = re.split(r"[.!?]+", text)
    # Filter out empty strings and very short fragments
    sentences = [s.strip() for s in sentences if len(s.strip()) > 5]
    return len(sentences)
