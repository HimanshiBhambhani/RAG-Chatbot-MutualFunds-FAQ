# Problem Statement: Mutual Fund FAQ Assistant (Facts-Only Q&A)

## Overview

The objective of this project is to build a **facts-only FAQ assistant** for mutual fund schemes, using **Groww** as the reference product context. The assistant will answer objective, verifiable queries related to mutual funds by retrieving information exclusively from official public sources, such as AMC (Asset Management Company) websites, AMFI, and SEBI.

The system must **strictly avoid** providing investment advice, opinions, or recommendations. Every response must include a single, clear source link and adhere to defined constraints around clarity, accuracy, and compliance.

---

## Objective

Design and implement a lightweight **Retrieval-Augmented Generation (RAG)**-based assistant that:

- Answers factual queries about mutual fund schemes
- Uses a curated corpus of official documents
- Provides concise, source-backed responses

---

## Target Users

- Retail investors comparing mutual fund schemes
- Customer support and content teams handling repetitive mutual fund queries

---

## Scope of Work

### 1. Corpus Definition

- Select one Asset Management Company (AMC)
- Collect **15–25 official public URLs**, including:
  - Scheme factsheets
  - KIM (Key Information Memorandum)
  - SID (Scheme Information Document)
  - AMC FAQ/help pages
  - AMFI/SEBI guidance pages
  - Statement and tax document download guides

### 2. Curated Corpus — 60 Fund URLs

**Source:** https://groww.in/mutual-funds/filter

#### Large Cap Funds (15)

| # | Fund Name | URL |
|---|-----------|-----|
| 1 | Nippon India Large Cap Fund Direct Growth | https://groww.in/mutual-funds/nippon-india-large-cap-fund-direct-growth |
| 2 | UTI Nifty 50 Index Fund Direct Growth | https://groww.in/mutual-funds/uti-nifty-fund-direct-growth |
| 3 | ICICI Prudential Large Cap Fund Direct Growth | https://groww.in/mutual-funds/icici-prudential-large-cap-fund-direct-growth |
| 4 | ICICI Prudential BHARAT 22 FOF Direct Growth | https://groww.in/mutual-funds/icici-prudential-bharat-22-fof-direct-growth |
| 5 | UTI Nifty Next 50 Index Fund Direct Growth | https://groww.in/mutual-funds/uti-nifty-next-50-index-fund-direct-growth |
| 6 | HDFC NIFTY 50 Index Fund Direct Growth | https://groww.in/mutual-funds/hdfc-nifty-50-index-fund-direct-growth |
| 7 | SBI Nifty Next 50 Index Fund Direct Growth | https://groww.in/mutual-funds/sbi-nifty-next-50-index-fund-direct-growth |
| 8 | ICICI Prudential Nifty Next 50 Index Direct Growth | https://groww.in/mutual-funds/icici-prudential-nifty-next-50-index-fund-direct-growth |
| 9 | Navi Nifty 50 Index Fund Direct Growth | https://groww.in/mutual-funds/navi-nifty-50-index-fund-direct-growth |
| 10 | SBI Large Cap Direct Plan Growth | https://groww.in/mutual-funds/sbi-large-cap-direct-plan-growth |
| 11 | ICICI Prudential Nifty 50 Index Direct Plan Growth | https://groww.in/mutual-funds/icici-prudential-nifty-index-fund-direct-growth |
| 12 | Parag Parikh Large Cap Fund Direct Growth | https://groww.in/mutual-funds/parag-parikh-large-cap-fund-direct-growth |
| 13 | HDFC BSE Sensex Index Fund Direct Growth | https://groww.in/mutual-funds/hdfc-bse-sensex-index-fund-direct-growth |
| 14 | DSP Nifty Next 50 Index Fund Direct Growth | https://groww.in/mutual-funds/dsp-nifty-next-50-index-fund-direct-growth |
| 15 | JioBlackRock Nifty 50 Index Fund Direct Growth | https://groww.in/mutual-funds/jioblackrock-nifty-50-index-fund-direct-growth |

#### Mid Cap Funds (15)

| # | Fund Name | URL |
|---|-----------|-----|
| 16 | HDFC Mid Cap Fund Direct Growth | https://groww.in/mutual-funds/hdfc-mid-cap-fund-direct-growth |
| 17 | Motilal Oswal Midcap Fund Direct Growth | https://groww.in/mutual-funds/motilal-oswal-most-focused-midcap-30-fund-direct-growth |
| 18 | Nippon India Growth Mid Cap Fund Direct Growth | https://groww.in/mutual-funds/nippon-india-growth-mid-cap-fund-direct-growth |
| 19 | WhiteOak Capital Mid Cap Fund Direct Growth | https://groww.in/mutual-funds/whiteoak-capital-mid-cap-fund-direct-growth |
| 20 | Edelweiss Mid Cap Direct Plan Growth | https://groww.in/mutual-funds/edelweiss-mid-and-small-cap-fund-direct-growth |
| 21 | Invesco India Mid Cap Fund Direct Growth | https://groww.in/mutual-funds/invesco-india-mid-cap-fund-direct-growth |
| 22 | Kotak Midcap Fund Direct Growth | https://groww.in/mutual-funds/kotak-emerging-equity-scheme-direct-growth |
| 23 | Motilal Oswal Nifty Midcap 150 Index Fund Direct Growth | https://groww.in/mutual-funds/motilal-oswal-nifty-midcap-150-index-fund-direct-growth |
| 24 | Quant Mid Cap Fund Direct Growth | https://groww.in/mutual-funds/quant-mid-cap-fund-direct-growth |
| 25 | SBI Mid Cap Direct Plan Growth | https://groww.in/mutual-funds/sbi-mid-cap-direct-plan-growth |
| 26 | Axis Midcap Direct Plan Growth | https://groww.in/mutual-funds/axis-midcap-fund-direct-growth |
| 27 | HSBC Midcap Fund Direct Growth | https://groww.in/mutual-funds/hsbc-midcap-fund-direct-growth |
| 28 | Nippon India Nifty Midcap 150 Index Fund Direct Growth | https://groww.in/mutual-funds/nippon-india-nifty-midcap-150-index-fund-direct-growth |
| 29 | ICICI Prudential Midcap Direct Plan Growth | https://groww.in/mutual-funds/icici-prudential-midcap-fund-direct-growth |
| 30 | JioBlackRock Nifty Midcap 150 Index Fund Direct Growth | https://groww.in/mutual-funds/jioblackrock-nifty-midcap-150-index-fund-direct-growth |

#### Small Cap Funds (13)

| # | Fund Name | URL |
|---|-----------|-----|
| 31 | Bandhan Small Cap Fund Direct Growth | https://groww.in/mutual-funds/bandhan-small-cap-fund-direct-growth |
| 32 | Nippon India Small Cap Fund Direct Growth | https://groww.in/mutual-funds/nippon-india-small-cap-fund-direct-growth |
| 33 | Quant Small Cap Fund Direct Plan Growth | https://groww.in/mutual-funds/quant-small-cap-fund-direct-plan-growth |
| 34 | Tata Small Cap Fund Direct Growth | https://groww.in/mutual-funds/tata-small-cap-fund-direct-growth |
| 35 | Axis Small Cap Fund Direct Growth | https://groww.in/mutual-funds/axis-small-cap-fund-direct-growth |
| 36 | Invesco India Smallcap Fund Direct Growth | https://groww.in/mutual-funds/invesco-india-smallcap-fund-direct-growth |
| 37 | SBI Small Cap Fund Direct Growth | https://groww.in/mutual-funds/sbi-small-midcap-fund-direct-growth |
| 38 | HDFC Small Cap Fund Direct Growth | https://groww.in/mutual-funds/hdfc-small-cap-fund-direct-growth |
| 39 | Motilal Oswal Small Cap Fund Direct Growth | https://groww.in/mutual-funds/motilal-oswal-small-cap-fund-direct-growth |
| 40 | Canara Robeco Small Cap Fund Direct Growth | https://groww.in/mutual-funds/canara-robeco-small-cap-fund-direct-growth |
| 41 | Bank of India Small Cap Fund Direct Growth | https://groww.in/mutual-funds/bank-of-india-small-cap-fund-direct-growth |
| 42 | Nippon India Nifty Smallcap 250 Index Fund Direct Growth | https://groww.in/mutual-funds/nippon-india-nifty-smallcap-250-index-fund-direct-growth |
| 43 | Mirae Asset Small Cap Fund Direct Growth | https://groww.in/mutual-funds/mirae-asset-small-cap-fund-direct-growth |

#### Flexi Cap / Focused Funds (7)

| # | Fund Name | URL |
|---|-----------|-----|
| 44 | Parag Parikh Flexi Cap Fund Direct Growth | https://groww.in/mutual-funds/parag-parikh-long-term-value-fund-direct-growth |
| 45 | HDFC Flexi Cap Direct Plan Growth | https://groww.in/mutual-funds/hdfc-equity-fund-direct-growth |
| 46 | Quant Flexi Cap Fund Direct Growth | https://groww.in/mutual-funds/quant-flexi-cap-fund-direct-growth |
| 47 | ICICI Prudential Flexicap Fund Direct Growth | https://groww.in/mutual-funds/icici-prudential-flexicap-fund-direct-growth |
| 48 | Motilal Oswal Flexi Cap Fund Direct Growth | https://groww.in/mutual-funds/motilal-oswal-most-focused-multicap-35-fund-direct-growth |
| 49 | HDFC Focused Fund Direct Growth | https://groww.in/mutual-funds/hdfc-focused-fund-direct-growth |
| 50 | SBI Focused Fund Direct Plan Growth | https://groww.in/mutual-funds/sbi-focused-fund-direct-plan-growth |

#### Defence Funds (5)

| # | Fund Name | URL |
|---|-----------|-----|
| 51 | HDFC Defence Fund Direct Growth | https://groww.in/mutual-funds/hdfc-defence-fund-direct-growth |
| 52 | Motilal Oswal Nifty India Defence Index Fund Direct Growth | https://groww.in/mutual-funds/motilal-oswal-nifty-india-defence-index-fund-direct-growth |
| 53 | ICICI Prudential Infrastructure Direct Growth | https://groww.in/mutual-funds/icici-prudential-infrastructure-fund-direct-growth |
| 54 | Nippon India Power & Infra Fund Direct Growth | https://groww.in/mutual-funds/nippon-india-power-infra-fund-direct-growth |
| 55 | Franklin Build India Fund Direct Growth | https://groww.in/mutual-funds/franklin-build-india-fund-direct-growth |

#### Equity / Thematic Funds (5)

| # | Fund Name | URL |
|---|-----------|-----|
| 56 | SBI PSU Direct Plan Growth | https://groww.in/mutual-funds/sbi-psu-fund-direct-growth |
| 57 | Aditya Birla Sun Life PSU Equity Fund Direct Growth | https://groww.in/mutual-funds/aditya-birla-sun-life-psu-equity-fund-direct-growth |
| 58 | Motilal Oswal Large and Midcap Fund Direct Growth | https://groww.in/mutual-funds/motilal-oswal-large-and-midcap-fund-direct-growth |
| 59 | Edelweiss US Technology Equity FoF Direct Growth | https://groww.in/mutual-funds/edelweiss-us-technology-equity-fof-direct-growth |
| 60 | Motilal Oswal BSE Enhanced Value Index Fund Direct Growth | https://groww.in/mutual-funds/motilal-oswal-bse-enhanced-value-index-fund-direct-growth |

---

### 3. FAQ Assistant Requirements

The assistant must answer **facts-only queries**, such as:

- Expense ratio of a scheme
- Exit load details
- Minimum SIP amount
- ELSS lock-in period
- Riskometer classification
- Benchmark index
- Fund manager name, qualification, and experience
- Process to download statements or capital gains reports

**Response Constraints:**

- Each response is limited to a **maximum of 3 sentences**
- Each response includes **exactly one citation link**
- Each response includes a footer:
  > "Last updated from sources: \<date\>"

### 4. Refusal Handling

The assistant must refuse non-factual or advisory queries, such as:

- "Should I invest in this fund?"
- "Which fund is better?"

Refusal responses should:

- Be polite and clearly worded
- Reinforce the facts-only limitation
- Provide a relevant educational link (e.g., AMFI or SEBI resource)

### 5. User Interface (Minimal)

The solution should include a simple interface with:

- A welcome message
- Three example questions
- A visible disclaimer:
  > "Facts-only. No investment advice."

---

## Constraints

### Data and Sources

- Use only official public sources (AMC, AMFI, SEBI)
- Do not use third-party blogs or aggregator websites

### Privacy and Security

Do not collect, store, or process:

- PAN or Aadhaar numbers
- Account numbers
- OTPs
- Email addresses or phone numbers

### Content Restrictions

- No investment advice or recommendations
- No performance comparisons or return calculations
- For performance-related queries, provide a link to the official factsheet only

### Transparency

- Responses must be short, factual, and verifiable
- Every answer must include a source link and last updated date

---

## Expected Deliverables

- **README Document**
  - Setup instructions
  - Selected AMC and schemes
  - Architecture overview (RAG approach)
  - Known limitations
- **Disclaimer Snippet**
  > "Facts-only. No investment advice."

---

## Success Criteria

- Accurate retrieval of factual mutual fund information
- Strict adherence to facts-only responses
- Consistent inclusion of valid source citations
- Proper refusal of advisory queries
- Clean, minimal, and user-friendly interface

---

## Summary

The goal is to build a **trustworthy, transparent, and compliant** mutual fund FAQ assistant that prioritizes **accuracy over intelligence**. The system should ensure that users receive only verified, source-backed financial information, without any advisory bias or speculative content.
