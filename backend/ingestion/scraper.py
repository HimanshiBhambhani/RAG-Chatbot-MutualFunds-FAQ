"""
Web Scraper for Groww mutual fund pages.
Fetches HTML content from fund URLs with rate limiting and error handling.
"""

import json
import logging
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

import requests

from backend.config import (
    RAW_DATA_DIR,
    SCRAPE_DELAY_SECONDS,
    USER_AGENT,
)
from backend.ingestion.fund_urls import get_all_fund_urls
from backend.ingestion.parser import extract_full_text, parse_fund_page

# ──────────────────────────────────────────────
# Logging Setup
# ──────────────────────────────────────────────
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger(__name__)


# ──────────────────────────────────────────────
# HTTP Session Configuration
# ──────────────────────────────────────────────
def _create_session() -> requests.Session:
    """Create a configured requests session with headers."""
    session = requests.Session()
    session.headers.update({
        "User-Agent": USER_AGENT,
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "Accept-Language": "en-US,en;q=0.9",
        "Accept-Encoding": "gzip, deflate",
        "Connection": "keep-alive",
        "Cache-Control": "no-cache",
    })
    return session


# ──────────────────────────────────────────────
# Core Scraping Functions
# ──────────────────────────────────────────────
def fetch_page(url: str, session: Optional[requests.Session] = None) -> Optional[str]:
    """
    Fetch a single fund page HTML.

    Args:
        url: The Groww mutual fund page URL.
        session: Optional requests session (creates new if None).

    Returns:
        HTML string if successful, None on failure.
    """
    if session is None:
        session = _create_session()

    try:
        response = session.get(url, timeout=30)
        response.raise_for_status()

        # Check for meaningful content (not empty/error page)
        if len(response.text) < 1000:
            logger.warning(f"Page too short ({len(response.text)} chars): {url}")
            return None

        return response.text

    except requests.exceptions.HTTPError as e:
        logger.error(f"HTTP error {e.response.status_code} for {url}: {e}")
        return None
    except requests.exceptions.ConnectionError as e:
        logger.error(f"Connection error for {url}: {e}")
        return None
    except requests.exceptions.Timeout:
        logger.error(f"Timeout fetching {url}")
        return None
    except requests.exceptions.RequestException as e:
        logger.error(f"Request failed for {url}: {e}")
        return None


def scrape_fund(fund: dict, session: requests.Session) -> Optional[dict]:
    """
    Scrape a single fund page and extract structured data.

    Args:
        fund: Fund dict with 'url', 'name', 'slug', 'category' keys.
        session: Requests session.

    Returns:
        Parsed fund data dict, or None on failure.
    """
    url = fund["url"]
    logger.info(f"Scraping: {fund['name']} ({url})")

    html = fetch_page(url, session)
    if html is None:
        logger.warning(f"SKIPPED (no HTML): {fund['name']}")
        return None

    # Parse structured fields from __NEXT_DATA__ JSON
    parsed_data = parse_fund_page(html, url)

    # Add metadata
    parsed_data["category"] = fund.get("category", parsed_data.get("category"))
    parsed_data["slug"] = fund["slug"]
    parsed_data["scraped_at"] = datetime.now(timezone.utc).isoformat()

    # If parser couldn't build full_text from JSON, fall back to HTML extraction
    if not parsed_data.get("full_text"):
        parsed_data["full_text"] = extract_full_text(html)

    # Use the canonical fund name from our list if parser couldn't extract
    if not parsed_data.get("fund_name"):
        parsed_data["fund_name"] = fund["name"]

    return parsed_data


def save_fund_data(fund_data: dict, output_dir: Path = RAW_DATA_DIR) -> Path:
    """
    Save parsed fund data as JSON.

    Args:
        fund_data: Parsed data dict.
        output_dir: Directory to save JSON files.

    Returns:
        Path to the saved JSON file.
    """
    output_dir.mkdir(parents=True, exist_ok=True)
    slug = fund_data.get("slug", "unknown")
    filepath = output_dir / f"{slug}.json"

    with open(filepath, "w", encoding="utf-8") as f:
        json.dump(fund_data, f, indent=2, ensure_ascii=False)

    return filepath


# ──────────────────────────────────────────────
# Main Scraping Pipeline
# ──────────────────────────────────────────────
def run_scraper(
    urls: Optional[list[dict]] = None,
    delay: float = SCRAPE_DELAY_SECONDS,
    output_dir: Path = RAW_DATA_DIR,
) -> dict:
    """
    Run the full scraping pipeline for all fund URLs.

    Args:
        urls: List of fund dicts. Uses all 60 if None.
        delay: Delay between requests in seconds.
        output_dir: Directory to save scraped data.

    Returns:
        Summary dict with success/failure counts.
    """
    if urls is None:
        urls = get_all_fund_urls()

    total = len(urls)
    logger.info(f"Starting scrape of {total} fund URLs...")
    logger.info(f"Output directory: {output_dir}")
    logger.info(f"Delay between requests: {delay}s")

    session = _create_session()
    success_count = 0
    failure_count = 0
    results = []

    for i, fund in enumerate(urls, 1):
        logger.info(f"[{i}/{total}] Processing: {fund['name']}")

        fund_data = scrape_fund(fund, session)

        if fund_data:
            filepath = save_fund_data(fund_data, output_dir)
            success_count += 1
            results.append({
                "name": fund["name"],
                "status": "success",
                "file": str(filepath),
            })
            logger.info(f"  ✓ Saved: {filepath.name}")
        else:
            failure_count += 1
            results.append({
                "name": fund["name"],
                "status": "failed",
                "url": fund["url"],
            })
            logger.warning(f"  ✗ Failed: {fund['name']}")

        # Rate limiting (skip delay on last item)
        if i < total:
            time.sleep(delay)

    # Summary
    summary = {
        "total": total,
        "success": success_count,
        "failed": failure_count,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "results": results,
    }

    # Save summary
    summary_path = output_dir / "_scrape_summary.json"
    with open(summary_path, "w", encoding="utf-8") as f:
        json.dump(summary, f, indent=2, ensure_ascii=False)

    logger.info(f"\n{'='*50}")
    logger.info(f"SCRAPE COMPLETE: {success_count}/{total} successful, {failure_count} failed")
    logger.info(f"Summary saved: {summary_path}")
    logger.info(f"{'='*50}")

    return summary


# ──────────────────────────────────────────────
# CLI Entry Point
# ──────────────────────────────────────────────
if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Scrape Groww mutual fund pages")
    parser.add_argument(
        "--limit",
        type=int,
        default=None,
        help="Limit number of URLs to scrape (for testing)",
    )
    parser.add_argument(
        "--delay",
        type=float,
        default=SCRAPE_DELAY_SECONDS,
        help=f"Delay between requests in seconds (default: {SCRAPE_DELAY_SECONDS})",
    )
    parser.add_argument(
        "--output",
        type=str,
        default=None,
        help="Output directory (default: data/raw/)",
    )
    args = parser.parse_args()

    # Get URLs
    all_urls = get_all_fund_urls()
    if args.limit:
        all_urls = all_urls[:args.limit]
        logger.info(f"Limited to first {args.limit} URLs (testing mode)")

    # Set output dir
    output = Path(args.output) if args.output else RAW_DATA_DIR

    # Run
    summary = run_scraper(urls=all_urls, delay=args.delay, output_dir=output)

    # Print final summary
    print(f"\n✅ Success: {summary['success']}")
    print(f"❌ Failed: {summary['failed']}")
    print(f"📁 Data saved to: {output}")
