# Edge Cases & Corner Scenarios

## RAG-Based Mutual Fund FAQ Assistant

This document catalogs all edge cases, corner scenarios, and boundary conditions that must be handled gracefully across the system. Each section maps to a component in the architecture.

---

## Table of Contents

1. [User Input & Query Edge Cases](#1-user-input--query-edge-cases)
2. [PII Detection Edge Cases](#2-pii-detection-edge-cases)
3. [Refusal Classification Edge Cases](#3-refusal-classification-edge-cases)
4. [Web Scraping & Ingestion Edge Cases](#4-web-scraping--ingestion-edge-cases)
5. [Chunking & Embedding Edge Cases](#5-chunking--embedding-edge-cases)
6. [Retrieval Edge Cases](#6-retrieval-edge-cases)
7. [LLM Generation Edge Cases](#7-llm-generation-edge-cases)
8. [Citation & Response Formatting Edge Cases](#8-citation--response-formatting-edge-cases)
9. [Scheduler & Pipeline Edge Cases](#9-scheduler--pipeline-edge-cases)
10. [Frontend / UI Edge Cases](#10-frontend--ui-edge-cases)
11. [API & Network Edge Cases](#11-api--network-edge-cases)
12. [Data Freshness & Consistency Edge Cases](#12-data-freshness--consistency-edge-cases)
13. [Multi-Provider LLM Edge Cases (Groq + Gemini)](#13-multi-provider-llm-edge-cases-groq--gemini)

---

## 1. User Input & Query Edge Cases

| # | Scenario | Example Input | Expected Behavior |
|---|----------|---------------|-------------------|
| 1.1 | Empty query | `""` or whitespace only | Return: "Please enter a question about mutual funds." |
| 1.2 | Extremely long query (>1000 chars) | Paragraph of text pasted | Truncate or reject with: "Please keep your question concise (under 300 characters)." |
| 1.3 | Non-English query | `"HDFC फंड का एक्सपेंस रेशियो क्या है?"` | Return: "I can only answer in English. Please rephrase your question." |
| 1.4 | Special characters / injection | `"; DROP TABLE funds; --"` | Sanitize input; treat as plain text; no DB injection risk (vector store) |
| 1.5 | Only numbers | `"12345"` | May trigger PII detection (OTP pattern); if not PII, ask user to clarify |
| 1.6 | URL as input | `"https://groww.in/mutual-funds/hdfc-defence-fund"` | Not a question — return: "Please ask a question. Example: What is the expense ratio of HDFC Defence Fund?" |
| 1.7 | Repeated identical queries (spam) | Same question 50 times in 1 min | Rate-limit: max 10 queries/min per session |
| 1.8 | Query about a fund NOT in corpus | `"What is the expense ratio of Zerodha Coin Fund?"` | Return: "I don't have information about this fund. I can answer about the 60 funds in my database." |
| 1.9 | Ambiguous fund name | `"HDFC fund expense ratio"` | Multiple HDFC funds exist — ask: "Multiple HDFC funds found. Did you mean HDFC Defence Fund, HDFC Mid Cap Fund, or HDFC Flexi Cap Fund?" |
| 1.10 | Typo in fund name | `"HDCF Defence Fund"` / `"Nipon India"` | Fuzzy match to closest fund name; ask for confirmation if similarity < threshold |
| 1.11 | Multi-part question | `"What is the expense ratio and exit load of SBI Small Cap?"` | Answer both facts if from same fund (still within 3 sentences) |
| 1.12 | Conversational follow-up | `"What about its fund manager?"` (no fund name) | Use session context from previous query; if no context, ask: "Which fund are you asking about?" |
| 1.13 | Greeting / small talk | `"Hello"` / `"Thank you"` | Return: "Hello! I can help you with mutual fund facts. Try asking about expense ratio, exit load, or fund manager details." |
| 1.14 | Profanity / offensive language | Abusive text | Return neutral: "I can only assist with mutual fund factual queries." |
| 1.15 | Query with markdown/HTML | `"**bold** <script>alert('xss')</script>"` | Strip HTML/markdown; treat as plain text |

---

## 2. PII Detection Edge Cases

| # | Scenario | Example Input | Expected Behavior |
|---|----------|---------------|-------------------|
| 2.1 | Valid PAN in query | `"My PAN is ABCDE1234F, check returns"` | Block immediately. Do not log the PAN. Return PII refusal. |
| 2.2 | PAN-like but not PAN | `"Fund code HDFC01234G"` | Should NOT trigger PII block (validate checksum pattern more strictly) |
| 2.3 | 12-digit number (Aadhaar-like) | `"AUM is 912361000000"` | Should NOT trigger — context is AUM value, not Aadhaar. Use word-boundary + context check. |
| 2.4 | Phone number in context | `"Customer care: 1800123456"` | Should NOT block if it's asking about fund house contact info |
| 2.5 | User shares email | `"Send report to my email user@example.com"` | Block. Return: "I cannot process personal information." |
| 2.6 | 10-digit number as AUM/NAV | `"Fund AUM is 5000000000"` | Should NOT trigger phone detection (check digit pattern [6-9] prefix) |
| 2.7 | OTP-like number in question | `"What is ELSS lock-in? Its 3 years right? 1234"` | `1234` matches OTP regex — but context suggests it's not an OTP. Use stricter matching: isolated 4-6 digits only |
| 2.8 | Multiple PII types in one query | `"PAN ABCDE1234F, Aadhaar 123456789012"` | Block on first match; do NOT echo back any PII in response |
| 2.9 | PII in non-ASCII | `"मेरा PAN ABCDE1234F है"` | Still detect PAN (regex works on ASCII portion) |
| 2.10 | Partial PII | `"My PAN starts with ABCDE"` | Don't block incomplete patterns; proceed normally |

### PII False Positive Mitigation

```python
# Context-aware checks to reduce false positives:
def is_likely_pii(match, full_query):
    # Exclude known financial numbers
    if "AUM" in full_query or "NAV" in full_query or "crore" in full_query:
        return False  # Likely a financial figure
    if "1800" in match:  # Toll-free numbers
        return False
    return True
```

---

## 3. Refusal Classification Edge Cases

| # | Scenario | Example Input | Should Refuse? | Notes |
|---|----------|---------------|----------------|-------|
| 3.1 | Direct advisory | "Should I invest in HDFC Mid Cap?" | ✅ Yes | Clear advisory intent |
| 3.2 | Subtle advisory | "Is HDFC Mid Cap a good choice for SIP?" | ✅ Yes | "good choice" = opinion |
| 3.3 | Performance comparison | "Which gives better returns: SBI or HDFC?" | ✅ Yes | Comparison = advisory |
| 3.4 | Factual with advisory word | "What is the recommended minimum SIP?" | ❌ No | "recommended" here means official min SIP, not advice |
| 3.5 | Future prediction | "Will NAV increase next month?" | ✅ Yes | Speculative |
| 3.6 | Return calculation | "If I invest 5000/month for 5 years?" | ✅ Yes | Calculation = advisory territory |
| 3.7 | Historical return fact | "What is the 3-year return of Axis Small Cap?" | ⚠️ Redirect | Provide link to source page only: "For performance data, visit: {url}" |
| 3.8 | Exit timing | "When should I exit this fund?" | ✅ Yes | Timing advice |
| 3.9 | Tax-related factual | "Is ELSS eligible for 80C deduction?" | ❌ No | Factual — general knowledge |
| 3.10 | Risk-related factual | "What is the riskometer of Quant Small Cap?" | ❌ No | Factual — from corpus |
| 3.11 | Sentiment-laced factual | "Why is expense ratio so high for this fund?" | ❌ No | Answer the factual part (what the ratio is); ignore the sentiment |
| 3.12 | Double intent | "What's the expense ratio and should I invest?" | ⚠️ Partial | Answer the factual part; refuse the advisory part |
| 3.13 | Polite refusal rejection | User responds: "I just want facts, not advice" after refusal | ❌ Allow | Re-process; if query was borderline, attempt factual answer |
| 3.14 | Coded advisory | "Which fund has best Sharpe ratio?" | ✅ Yes | Implicit comparison/recommendation |
| 3.15 | Process question | "How do I invest in mutual funds?" | ❌ No | General process info — can answer or redirect to AMFI |

---

## 4. Web Scraping & Ingestion Edge Cases

| # | Scenario | Impact | Mitigation |
|---|----------|--------|------------|
| 4.1 | Groww returns 404 for a fund URL | Missing data for 1 fund | Log error; skip fund; use last-good cached data; alert admin |
| 4.2 | Groww returns 5xx (server error) | Scraper hangs/fails | Retry with exponential backoff (3 attempts, 5s/15s/45s) |
| 4.3 | Groww changes HTML structure | Parser extracts wrong/empty data | Validate extracted fields; if >50% empty, halt pipeline + alert |
| 4.4 | Groww adds CAPTCHA or rate-limiting | All scrapes fail | Detect 429/403; pause; rotate user-agent; consider Playwright |
| 4.5 | Fund page has no expense ratio listed | Missing key field | Store as `null`; when queried, return: "This information is not available on the source page." |
| 4.6 | Fund merged/renamed on Groww | Old URL redirects or 404s | Follow redirects (301/302); update URL in corpus; log change |
| 4.7 | Fund discontinued (NFO period ended) | URL may become stale | Mark as "discontinued" in metadata; answer with disclaimer |
| 4.8 | Extremely large page (>100KB HTML) | Parser slow/OOM | Set max page size limit; only parse relevant sections |
| 4.9 | Page partially loaded (JS content missing) | Incomplete data | Detect incomplete extractions; switch to Playwright for that URL |
| 4.10 | Network timeout during scrape | Incomplete batch | Per-URL timeout (30s); mark failed URLs; continue with others |
| 4.11 | Duplicate content across pages | Redundant chunks | Deduplication via content hash before indexing |
| 4.12 | Groww A/B tests different page layouts | Inconsistent parsing | Maintain multiple parser strategies; select based on page markers |
| 4.13 | Unicode/encoding issues in scraped text | Garbled text in store | Enforce UTF-8 decode; strip non-printable chars |
| 4.14 | Scraped data contains disclaimer text | Noise in chunks | Filter out common disclaimer patterns during parsing |

---

## 5. Chunking & Embedding Edge Cases

| # | Scenario | Impact | Mitigation |
|---|----------|--------|------------|
| 5.1 | Single field shorter than chunk size | Entire "exit_load" is 10 words | Keep as standalone chunk; don't merge unrelated sections |
| 5.2 | Very long holdings table (50+ rows) | Multiple chunks for one section | Split by rows; each chunk gets same metadata `section: "holdings"` |
| 5.3 | Overlapping chunks create duplicated answers | LLM sees same info twice in context | Deduplicate retrieved chunks before passing to LLM |
| 5.4 | Embedding model returns error/timeout | Chunks not indexed | Retry embedding; batch in smaller sizes; log failed chunks |
| 5.5 | Chunk boundary splits a sentence | Partial info in chunk | Overlap (100 tokens) should prevent this; validate chunk coherence |
| 5.6 | Metadata mismatch after re-index | Old metadata persists | Clear collection before full re-index (daily); or use upsert by ID |
| 5.7 | Empty chunk after cleaning | Noise-only text got cleaned to nothing | Skip empty chunks; don't index |
| 5.8 | Numbers/tables don't embed well | Semantic search misses numeric queries | Add keyword search fallback for numeric fields (NAV, AUM, expense ratio) |
| 5.9 | Fund name spelled differently in different sections | Chunks from same fund get different metadata | Normalize fund name at parse time using canonical mapping |
| 5.10 | Embedding dimensionality mismatch after model change | Vector store corrupted | Full re-index required when changing embedding model; version the collection |

---

## 6. Retrieval Edge Cases

| # | Scenario | Example | Expected Behavior |
|---|----------|---------|-------------------|
| 6.1 | Query matches no chunks (similarity < threshold) | "What is the GDP of India?" | Return: "I don't have information about this topic. I can only answer questions about mutual fund schemes." |
| 6.2 | Top-K chunks are from different funds | "expense ratio" (generic) | Multiple fund chunks returned — disambiguate or ask user which fund |
| 6.3 | All retrieved chunks are stale (>7 days old) | Scheduler failed for a week | Include warning: "Data may be outdated (last updated: {date}). Please verify on Groww." |
| 6.4 | Retrieved chunk has `null` value for queried field | Expense ratio not on page | Return: "This information is not currently available on the source page." + provide link |
| 6.5 | Semantic search returns irrelevant chunks | "SBI" matches "Aditya Birla Sun Life" via partial match | Apply fund name filter in metadata before semantic search |
| 6.6 | Two funds with very similar names | "Nippon India Large Cap" vs "Nippon India Growth Mid Cap" | Use exact name matching in metadata filter when fund name is clear |
| 6.7 | Abbreviation not expanded | "PPFAS" / "PPFCF" | Query reformulator must map `PPFAS → Parag Parikh Flexi Cap Fund` |
| 6.8 | Query is about fund category, not specific fund | "Best large cap funds list" | Refuse (advisory) OR list funds in that category without ranking |
| 6.9 | ChromaDB collection is empty (first run before ingestion) | Fresh deploy, no data | Return: "System is initializing. Please try again in a few minutes." |
| 6.10 | Vector store file corrupted | ChromaDB persistence issue | Detect corruption on startup; trigger re-index from last good cache |

---

## 7. LLM Generation Edge Cases

| # | Scenario | Impact | Mitigation |
|---|----------|--------|------------|
| 7.1 | LLM ignores system prompt and gives advice | Compliance violation | Post-response validator checks for advisory keywords; if detected, replace with refusal |
| 7.2 | LLM generates >3 sentences | Response too long | Hard-truncate at 3rd sentence (period + space); add validator |
| 7.3 | LLM hallucinates a URL not in context | False citation | Validate citation URL against corpus URLs; reject if not in list |
| 7.4 | LLM returns empty response | No answer shown | Detect empty; return fallback: "I couldn't find an answer. Please try rephrasing." |
| 7.5 | LLM response is in wrong language | User confusion | Detect non-English chars; regenerate with explicit English instruction |
| 7.6 | LLM adds disclaimer/caveats not in prompt | Extra boilerplate | Strip known LLM disclaimers ("As an AI...", "I should note...") |
| 7.7 | LLM compares funds despite instruction | Compliance violation | Post-filter: detect comparison patterns; replace with refusal |
| 7.8 | LLM leaks system prompt content | Security concern | Never include raw prompt in response; test with prompt injection attacks |
| 7.9 | LLM calculates returns | Advisory violation | Detect numeric calculations in response; refuse if return-related |
| 7.10 | Token limit exceeded (context too large) | API error | Trim context to fit model's limit; prioritize highest-similarity chunks |
| 7.11 | LLM returns JSON/code instead of natural language | Broken UX | Detect non-prose responses; regenerate or return fallback |
| 7.12 | Prompt injection via user query | `"Ignore previous instructions..."` | Sanitize input; use separate system/user message roles; test adversarial inputs |

---

## 8. Citation & Response Formatting Edge Cases

| # | Scenario | Impact | Mitigation |
|---|----------|--------|------------|
| 8.1 | Source URL is dead (fund page removed) | Broken link in response | Periodic URL health check; mark dead URLs; use alternative source or caveat |
| 8.2 | Multiple chunks from same URL | Redundant citation | Only cite once; deduplicate |
| 8.3 | No `last_scraped` date in metadata | Missing footer | Default to system deploy date; flag as stale |
| 8.4 | Citation URL doesn't match the fund asked about | Wrong source | Validate: citation URL must contain fund slug matching the query |
| 8.5 | Response contains special chars that break UI | Rendering issue | Escape markdown/HTML in response before display |
| 8.6 | LLM puts citation in middle of response | Inconsistent format | Post-process: extract URL → move to end of answer → format consistently |
| 8.7 | Footer date is in wrong format | `"2026/06/04"` instead of `"2026-06-04"` | Enforce ISO format in prompt + post-process validation |

---

## 9. Scheduler & Pipeline Edge Cases

| # | Scenario | Impact | Mitigation |
|---|----------|--------|------------|
| 9.1 | Scheduler fires but previous run still ongoing | Concurrent writes to vector store | Mutex/lock: skip run if lock file exists |
| 9.2 | Scheduler fails silently at 2 AM | Data goes stale indefinitely | Health check: if `last_scraped` > 24h old, emit warning in responses |
| 9.3 | Partial pipeline failure (30/60 URLs scraped) | Incomplete data | Keep old chunks for failed URLs; only replace successfully scraped ones |
| 9.4 | Time zone mismatch | Scheduler runs at wrong time | Explicitly set timezone in config: `Asia/Kolkata` |
| 9.5 | Server restart kills scheduler | Missed daily run | Use systemd/cron for resilience; or detect missed run on startup |
| 9.6 | Disk full during pipeline | ChromaDB write fails | Check disk space before run; alert if <500MB free |
| 9.7 | Embedding API rate-limited during batch | Partial indexing | Batch with delays; exponential backoff; resume from last checkpoint |
| 9.8 | Pipeline completes but vector store is now worse (parser regression) | Quality drop | Run validation queries post-pipeline; rollback if accuracy drops |
| 9.9 | GitHub Actions cron drift | Runs inconsistently | Use `workflow_dispatch` for manual trigger as backup |
| 9.10 | APScheduler thread dies in-process | Silent failure | APScheduler `misfire_grace_time` + health endpoint monitoring |

---

## 10. Frontend / UI Edge Cases

| # | Scenario | Impact | Mitigation |
|---|----------|--------|------------|
| 10.1 | User submits query while previous is still loading | Race condition / double response | Disable input during loading; show spinner; queue or cancel previous |
| 10.2 | Extremely long response displayed | UI overflow | CSS overflow handling; truncate with "show more" if >3 sentences slip through |
| 10.3 | Citation link not clickable | Bad UX | Ensure URL is rendered as hyperlink with `target="_blank"` |
| 10.4 | Session state lost on page refresh (Streamlit) | Chat history gone | Use `st.session_state`; persist last 10 messages |
| 10.5 | User pastes multi-line text in input | Unexpected behavior | Flatten to single line; or support multi-line with Shift+Enter |
| 10.6 | Mobile responsiveness | UI broken on phone | Use responsive CSS; test at 375px width |
| 10.7 | Disclaimer not visible (scrolled off) | Compliance risk | Sticky disclaimer at top/bottom; always visible |
| 10.8 | Browser back button clears state | User loses context | Handle navigation; persist state in URL params or localStorage |
| 10.9 | Copy-paste includes hidden characters | Unicode zero-width chars in query | Strip invisible characters before processing |
| 10.10 | Dark mode rendering issues | Text invisible on dark background | Support both themes; test contrast ratios |

### Next.js Specific Edge Cases

| # | Scenario | Impact | Mitigation |
|---|----------|--------|------------|
| 10.11 | FastAPI backend unreachable from frontend | No responses | Show error banner: "Service temporarily unavailable"; retry button |
| 10.12 | Streaming response disconnects mid-stream | Partial answer shown | Detect incomplete stream; show warning + retry option |
| 10.13 | CORS issues between Next.js and FastAPI | API calls blocked | Configure FastAPI CORS middleware with frontend origin |
| 10.14 | SSR hydration mismatch | React error in console | Use client components for chat; avoid server-side state |

---

## 11. API & Network Edge Cases

| # | Scenario | Impact | Mitigation |
|---|----------|--------|------------|
| 11.1 | Groq API returns 429 (rate limit) | No LLM response | Fallback to Gemini; if both limited, return: "High traffic. Please try again shortly." |
| 11.2 | Gemini API returns 500 | Service unavailable | Retry once; fallback to Groq; show error if both fail |
| 11.3 | Network timeout to LLM provider (>10s) | User waits forever | Set timeout at 10s; return fallback response |
| 11.4 | API key expired or invalid | All queries fail | Validate API key on startup; clear error message in logs |
| 11.5 | Response payload too large from LLM | Memory/bandwidth issue | Set `max_tokens` limit in API call (500 tokens max for 3 sentences) |
| 11.6 | SSL certificate error | Connection refused | Retry; log error; use latest CA bundle |
| 11.7 | DNS resolution failure | Can't reach APIs | Retry with backoff; return cached response if available |
| 11.8 | Concurrent users overwhelming single-process app | Slow/crashed app | Use async (FastAPI) + connection pooling; scale horizontally |

---

## 12. Data Freshness & Consistency Edge Cases

| # | Scenario | Impact | Mitigation |
|---|----------|--------|------------|
| 12.1 | User asks about today's NAV but last scrape was yesterday | Stale data | Footer clearly shows date; response: "As of {date}, NAV is..." |
| 12.2 | Fund changes expense ratio mid-day | Stale until next scrape | Acceptable limitation; document in response footer |
| 12.3 | New fund manager appointed but not yet scraped | Wrong fund manager info | Daily scrape minimizes window; disclaim with date |
| 12.4 | Fund merged into another (corporate action) | Old fund no longer exists | Detect 301 redirect to new page; update corpus; notify user |
| 12.5 | Groww shows different data than AMC website | Source discrepancy | Document that Groww is sole source; don't cross-validate |
| 12.6 | Multiple conflicting chunks for same field | Which is correct? | Use chunk with latest `last_scraped`; if same date, use first retrieved |
| 12.7 | Holiday (market closed) — NAV unchanged | Redundant scrape | Still run pipeline (other fields may change); optimization: diff-check |
| 12.8 | Backdated NAV shown (T+1 settlement) | User confusion about "today's" NAV | Always cite the date explicitly in response |

---

## 13. Multi-Provider LLM Edge Cases (Groq + Gemini)

| # | Scenario | Impact | Mitigation |
|---|----------|--------|------------|
| 13.1 | Groq and Gemini give different answers for same query | Inconsistency | Stick to primary provider per session; don't switch mid-conversation |
| 13.2 | Groq free tier exhausted for the day | All queries fail if no fallback | Auto-switch to Gemini; track daily usage |
| 13.3 | Gemini returns safety-filtered response | Empty/refused answer for valid factual query | Detect safety filter; retry with Groq; adjust prompt if needed |
| 13.4 | Model version deprecated | API returns error | Pin model versions in config; update quarterly |
| 13.5 | Response quality differs between providers | Inconsistent UX | Normalize output with post-processing; validate against format rules |
| 13.6 | Groq returns faster but lower quality answer | Trade-off | Use response validator; if quality check fails, retry with Gemini |
| 13.7 | Both providers down simultaneously | Complete outage | Cache last 50 FAQ answers; serve from cache with "cached response" disclaimer |
| 13.8 | Provider changes pricing/limits without notice | Cost spike / failure | Monitor usage dashboard; set spend alerts; maintain fallback |

---

## Summary: Guardrail Layers

```
User Input
    │
    ▼
┌────────────────────────────┐
│  Layer 1: Input Sanitization│  ← Empty, too long, special chars, HTML
└────────────┬───────────────┘
             │
             ▼
┌────────────────────────────┐
│  Layer 2: PII Detection    │  ← PAN, Aadhaar, phone, email, OTP
└────────────┬───────────────┘
             │
             ▼
┌────────────────────────────┐
│  Layer 3: Refusal Classifier│  ← Advisory, comparisons, predictions
└────────────┬───────────────┘
             │
             ▼
┌────────────────────────────┐
│  Layer 4: Query Validation │  ← Length, language, fund existence
└────────────┬───────────────┘
             │
             ▼
┌────────────────────────────┐
│  Layer 5: RAG Pipeline     │  ← Retrieval + Generation
└────────────┬───────────────┘
             │
             ▼
┌────────────────────────────┐
│  Layer 6: Response Validator│  ← Length, citation, no-advice check
└────────────┬───────────────┘
             │
             ▼
┌────────────────────────────┐
│  Layer 7: Format & Deliver │  ← Footer, disclaimer, UI rendering
└────────────────────────────┘
```

---

## Test Matrix Template

Use this template to validate each edge case during Phase 4 & Phase 7:

| Test ID | Category | Input | Expected Output | Actual Output | Pass/Fail |
|---------|----------|-------|-----------------|---------------|-----------|
| EC-1.1 | Input | `""` | "Please enter a question..." | | |
| EC-2.1 | PII | `"PAN ABCDE1234F"` | PII refusal | | |
| EC-3.1 | Refusal | `"Should I invest?"` | Advisory refusal | | |
| EC-6.1 | Retrieval | `"GDP of India"` | Out-of-scope response | | |
| EC-7.1 | Generation | LLM gives advice | Post-validator catches + replaces | | |
| ... | ... | ... | ... | | |

---

## Priority Matrix

| Priority | Count | Categories |
|----------|-------|------------|
| 🔴 Critical (must handle before launch) | 25 | PII blocking, advisory refusal, LLM hallucination, prompt injection |
| 🟡 High (handle in MVP) | 30 | Input validation, retrieval misses, citation accuracy, API failures |
| 🟢 Medium (handle post-MVP) | 20 | Ambiguous queries, typo handling, session context, mobile UX |
| ⚪ Low (nice to have) | 15 | Dark mode, caching, A/B page parsing, multi-language |

---

## Implementation Checklist

- [ ] All Layer 1–3 edge cases handled before RAG pipeline is invoked
- [ ] Post-response validator catches LLM violations (advice, length, hallucinated URLs)
- [ ] Fallback mechanism tested: Groq → Gemini → cached response → error message
- [ ] PII regex tested against 50+ samples (25 true PII + 25 false positives)
- [ ] Advisory classifier tested against 50+ samples (25 advisory + 25 factual)
- [ ] Scheduler failure detection + stale-data warning in responses
- [ ] UI handles loading states, errors, and empty states gracefully
- [ ] Rate limiting prevents spam/abuse
- [ ] All citation URLs validated against known corpus
- [ ] Prompt injection attacks tested and mitigated
