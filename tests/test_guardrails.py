"""
Phase 4 Test Script: Guardrails & Refusal Logic
Tests PII detection, advisory refusal, off-topic handling, and response validation.
"""

import sys
sys.path.insert(0, ".")

from backend.guardrails.pii_detector import detect_pii, contains_pii
from backend.guardrails.refusal import classify_query
from backend.guardrails.validator import validate_response, ValidationResult


def test_section(title: str):
    print(f"\n{'='*60}")
    print(f"  {title}")
    print(f"{'='*60}")


def test_pii_detection():
    test_section("PII Detection Tests")
    
    test_cases = [
        # (query, should_detect, description)
        ("My PAN is ABCDE1234F", True, "PAN number"),
        ("Aadhaar: 9234 5678 9012", True, "Aadhaar with spaces"),
        ("Call me at 9876543210", True, "Phone number"),
        ("Email: john@example.com", True, "Email address"),
        ("My OTP: 456789", True, "OTP code"),
        ("my pan number is", True, "PII context without value"),
        ("+91 9876543210 is my number", True, "Phone with +91"),
        ("What is the NAV of HDFC fund?", False, "Normal query"),
        ("expense ratio of SBI Small Cap", False, "Normal query"),
        ("fund manager of Axis Midcap", False, "Normal query"),
        ("AUM is ₹9123 crore", False, "Financial figure not PII"),
        ("HDFC Defence Fund Direct Growth", False, "Fund name not PII"),
    ]
    
    passed = 0
    failed = 0
    
    for query, should_detect, desc in test_cases:
        detected = contains_pii(query)
        status = "✅" if detected == should_detect else "❌"
        if detected == should_detect:
            passed += 1
        else:
            failed += 1
        print(f"  {status} [{desc}] Query: '{query[:40]}...' → Detected: {detected} (expected: {should_detect})")
    
    print(f"\n  Results: {passed}/{passed+failed} passed")
    return passed, failed


def test_advisory_refusal():
    test_section("Advisory Refusal Tests")
    
    test_cases = [
        # (query, expected_classification, description)
        ("Should I invest in HDFC Defence Fund?", "advisory", "Direct advice seek"),
        ("Which fund is better for long term?", "advisory", "Comparison advice"),
        ("Recommend a good mutual fund", "advisory", "Recommendation request"),
        ("Will this fund give good returns?", "advisory", "Return prediction"),
        ("Is it safe to invest in small cap?", "advisory", "Safety advice"),
        ("Compare performance of HDFC vs SBI", "advisory", "Performance comparison"),
        ("Best fund to buy for retirement", "advisory", "Best fund advice"),
        ("Buy or sell Axis Midcap?", "advisory", "Buy/sell advice"),
        ("How much should I invest monthly?", "advisory", "Amount advice"),
        ("Suggest a fund for tax saving", "advisory", "Suggestion request"),
        ("What is the expense ratio of HDFC Defence Fund?", None, "Valid factual query"),
        ("Who manages SBI Small Cap Fund?", None, "Valid factual query"),
        ("What is the exit load for Axis Midcap?", None, "Valid factual query"),
        ("NAV of Motilal Oswal Midcap Fund", None, "Valid factual query"),
        ("Tell me about the benchmark of ICICI fund", None, "Valid factual query"),
        ("What is the AUM of Kotak Small Cap?", None, "Valid factual query"),
        ("What's the weather today?", "off_topic", "Off-topic query"),
        ("Tell me a joke", "off_topic", "Off-topic query"),
        ("Hello", "greeting", "Simple greeting"),
        ("Hi there", "greeting", "Simple greeting"),
        ("Will it definitely grow in future?", "advisory", "Growth prediction"),
        ("This fund guarantees returns right?", "advisory", "Guaranteed returns"),
    ]
    
    passed = 0
    failed = 0
    
    for query, expected, desc in test_cases:
        result = classify_query(query)
        status = "✅" if result == expected else "❌"
        if result == expected:
            passed += 1
        else:
            failed += 1
        print(f"  {status} [{desc}] Query: '{query[:45]}' → Got: {result} (expected: {expected})")
    
    print(f"\n  Results: {passed}/{passed+failed} passed")
    return passed, failed


def test_response_validation():
    test_section("Response Validation Tests")
    
    test_cases = [
        # (response, source_url, should_be_valid, description)
        (
            "The expense ratio of HDFC Defence Fund is 0.83%.\n\nSource: https://groww.in/mutual-funds/hdfc-defence-fund\nLast updated from sources: 04 June 2026",
            "https://groww.in/mutual-funds/hdfc-defence-fund",
            True,
            "Valid response with citation",
        ),
        (
            "I recommend you invest in this fund as it will give great returns.\n\nSource: https://groww.in/test",
            "https://groww.in/test",
            False,
            "Advisory language leaked",
        ),
        (
            "You should buy this fund immediately for guaranteed returns.",
            "",
            False,
            "Strong advisory + no citation",
        ),
        (
            "",
            "",
            False,
            "Empty response",
        ),
        (
            "The NAV is ₹28.44 as of the last scrape.\n\nSource: https://groww.in/mutual-funds/hdfc-defence-fund\nLast updated from sources: 04 June 2026",
            "https://groww.in/mutual-funds/hdfc-defence-fund",
            True,
            "Valid short response",
        ),
    ]
    
    passed = 0
    failed = 0
    
    for response, source_url, should_be_valid, desc in test_cases:
        result = validate_response(response, source_url)
        is_valid = result.is_valid
        status = "✅" if is_valid == should_be_valid else "❌"
        if is_valid == should_be_valid:
            passed += 1
        else:
            failed += 1
        detail = f"issues={result.issues}" if result.issues else f"warnings={result.warnings}"
        print(f"  {status} [{desc}] Valid: {is_valid} (expected: {should_be_valid}) | {detail}")
    
    print(f"\n  Results: {passed}/{passed+failed} passed")
    return passed, failed


def test_end_to_end_guardrails():
    """Test guardrails integrated in the chain (without LLM calls for blocked queries)."""
    test_section("End-to-End Guardrail Integration")
    
    from backend.guardrails.pii_detector import contains_pii, get_pii_refusal
    from backend.guardrails.refusal import classify_query, get_refusal_response
    
    test_cases = [
        ("My PAN is ABCDE1234F, what is NAV?", "pii", "PII should block before RAG"),
        ("Should I invest in HDFC fund?", "advisory", "Advisory should refuse"),
        ("Hello!", "greeting", "Greeting handled gracefully"),
        ("What's the weather?", "off_topic", "Off-topic refused"),
        ("What is the expense ratio of HDFC Defence Fund?", None, "Valid → passes to RAG"),
    ]
    
    passed = 0
    failed = 0
    
    for query, expected_block, desc in test_cases:
        # Simulate the chain's pre-query logic
        blocked_by = None
        if contains_pii(query):
            blocked_by = "pii"
        else:
            classification = classify_query(query)
            if classification:
                blocked_by = classification
        
        status = "✅" if blocked_by == expected_block else "❌"
        if blocked_by == expected_block:
            passed += 1
        else:
            failed += 1
        print(f"  {status} [{desc}] Query: '{query[:40]}' → Blocked: {blocked_by} (expected: {expected_block})")
    
    print(f"\n  Results: {passed}/{passed+failed} passed")
    return passed, failed


if __name__ == "__main__":
    print("\n" + "🛡️" * 3 + " PHASE 4: GUARDRAILS TEST SUITE " + "🛡️" * 3)
    
    total_passed = 0
    total_failed = 0
    
    p, f = test_pii_detection()
    total_passed += p
    total_failed += f
    
    p, f = test_advisory_refusal()
    total_passed += p
    total_failed += f
    
    p, f = test_response_validation()
    total_passed += p
    total_failed += f
    
    p, f = test_end_to_end_guardrails()
    total_passed += p
    total_failed += f
    
    print(f"\n{'='*60}")
    print(f"  TOTAL: {total_passed}/{total_passed+total_failed} tests passed")
    if total_failed == 0:
        print("  ✅ ALL TESTS PASSED")
    else:
        print(f"  ⚠️  {total_failed} tests failed")
    print(f"{'='*60}\n")
