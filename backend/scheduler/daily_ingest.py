"""
Daily Ingestion Scheduler.
Runs the full scraping + chunking + embedding pipeline at 10:00 AM IST daily.

Usage:
    # Run scheduler (stays running, triggers at 10:00 AM IST daily):
    python -m backend.scheduler.daily_ingest

    # Run once immediately (for testing):
    python -m backend.scheduler.daily_ingest --now

    # Run with reset (rebuild entire vector store):
    python -m backend.scheduler.daily_ingest --now --reset
"""

import argparse
import logging
import shutil
import sys
import time
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

from apscheduler.schedulers.blocking import BlockingScheduler
from apscheduler.triggers.cron import CronTrigger

# Ensure project root is on path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from backend.config import RAW_DATA_DIR, VECTORDB_DIR
from backend.ingestion.scraper import run_scraper
from backend.ingestion.pipeline import run_pipeline

# ──────────────────────────────────────────────
# Logging
# ──────────────────────────────────────────────
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger("daily_ingest")

# Timezone
IST = ZoneInfo("Asia/Kolkata")


# ──────────────────────────────────────────────
# Backup Logic
# ──────────────────────────────────────────────

def backup_vectordb() -> Path | None:
    """
    Create a backup of the current vector DB before refreshing.
    Returns the backup path or None if no existing DB.
    """
    if not VECTORDB_DIR.exists():
        return None

    backup_dir = VECTORDB_DIR.parent / "vectordb_backup"
    if backup_dir.exists():
        shutil.rmtree(backup_dir)

    shutil.copytree(VECTORDB_DIR, backup_dir)
    logger.info(f"Vector DB backed up to: {backup_dir}")
    return backup_dir


def restore_backup(backup_dir: Path):
    """Restore vector DB from backup in case of failure."""
    if backup_dir and backup_dir.exists():
        if VECTORDB_DIR.exists():
            shutil.rmtree(VECTORDB_DIR)
        shutil.copytree(backup_dir, VECTORDB_DIR)
        logger.info("Vector DB restored from backup.")


# ──────────────────────────────────────────────
# Daily Ingestion Job
# ──────────────────────────────────────────────

def daily_ingestion(reset: bool = False):
    """
    Full daily ingestion pipeline:
    1. Backup existing vector DB
    2. Scrape all 60 fund URLs
    3. Chunk + embed → update ChromaDB
    4. Log results

    Args:
        reset: If True, rebuild the entire vector store from scratch.
    """
    run_start = datetime.now(IST)
    logger.info("=" * 60)
    logger.info(f"  DAILY INGESTION STARTED: {run_start.strftime('%Y-%m-%d %H:%M:%S IST')}")
    logger.info("=" * 60)

    # Step 1: Backup
    backup_dir = None
    try:
        backup_dir = backup_vectordb()
    except Exception as e:
        logger.warning(f"Backup failed (continuing anyway): {e}")

    # Step 2: Scrape
    logger.info("\n📡 Step 1/2: Scraping fund data from Groww...")
    try:
        scrape_result = run_scraper()
        scrape_success = scrape_result.get("success_count", 0)
        scrape_failed = scrape_result.get("failure_count", 0)
        logger.info(f"  Scrape complete: {scrape_success} success, {scrape_failed} failed")

        if scrape_success == 0:
            logger.error("All scrapes failed! Aborting pipeline.")
            if backup_dir:
                restore_backup(backup_dir)
            return {"status": "failed", "reason": "all scrapes failed"}

    except Exception as e:
        logger.error(f"Scraper crashed: {e}")
        if backup_dir:
            restore_backup(backup_dir)
        return {"status": "failed", "reason": str(e)}

    # Step 3: Pipeline (chunk + embed + index)
    logger.info("\n🔄 Step 2/2: Running chunking + embedding pipeline...")
    try:
        pipeline_result = run_pipeline(
            reset=reset,
            embedding_provider=None,  # Use config default (gemini)
        )
        chunks_indexed = pipeline_result.get("chunks_added_to_store", 0)
        total_in_store = pipeline_result.get("collection_total", 0)
        elapsed = pipeline_result.get("elapsed_seconds", 0)

        logger.info(f"  Pipeline complete: {chunks_indexed} new chunks indexed")
        logger.info(f"  Total in store: {total_in_store}")
        logger.info(f"  Elapsed: {elapsed}s")

    except Exception as e:
        logger.error(f"Pipeline crashed: {e}")
        if backup_dir:
            restore_backup(backup_dir)
        return {"status": "failed", "reason": str(e)}

    # Step 4: Summary
    run_end = datetime.now(IST)
    duration = (run_end - run_start).total_seconds()

    summary = {
        "status": "success",
        "started_at": run_start.isoformat(),
        "finished_at": run_end.isoformat(),
        "duration_seconds": round(duration, 1),
        "scrape_success": scrape_success,
        "scrape_failed": scrape_failed,
        "chunks_indexed": chunks_indexed,
        "total_in_store": total_in_store,
    }

    logger.info("")
    logger.info("=" * 60)
    logger.info("  DAILY INGESTION COMPLETE")
    logger.info("=" * 60)
    for k, v in summary.items():
        logger.info(f"    {k}: {v}")
    logger.info("")

    return summary


# ──────────────────────────────────────────────
# Scheduler Setup
# ──────────────────────────────────────────────

def start_scheduler():
    """
    Start the APScheduler with a cron trigger at 10:00 AM IST daily.
    This process stays running and triggers the ingestion job.
    """
    scheduler = BlockingScheduler(timezone=IST)

    scheduler.add_job(
        daily_ingestion,
        trigger=CronTrigger(hour=10, minute=0, timezone=IST),
        id="daily_ingestion",
        name="Daily Fund Data Refresh (10:00 AM IST)",
        misfire_grace_time=3600,  # Allow up to 1 hour delay
    )

    logger.info("")
    logger.info("🕐 Scheduler started — daily ingestion at 10:00 AM IST")
    logger.info("   Press Ctrl+C to stop.")
    logger.info("")

    next_run = scheduler.get_job("daily_ingestion").next_run_time
    logger.info(f"   Next run: {next_run.strftime('%Y-%m-%d %H:%M:%S %Z')}")
    logger.info("")

    try:
        scheduler.start()
    except (KeyboardInterrupt, SystemExit):
        logger.info("\nScheduler stopped.")
        scheduler.shutdown()


# ──────────────────────────────────────────────
# CLI Entry Point
# ──────────────────────────────────────────────

if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Daily ingestion scheduler for Mutual Fund FAQ Assistant"
    )
    parser.add_argument(
        "--now",
        action="store_true",
        help="Run ingestion immediately (don't start scheduler)",
    )
    parser.add_argument(
        "--reset",
        action="store_true",
        help="Reset (rebuild) the entire vector store",
    )
    args = parser.parse_args()

    if args.now:
        logger.info("Running ingestion immediately (--now flag)")
        result = daily_ingestion(reset=args.reset)
        status = result.get("status", "unknown")
        if status == "success":
            print(f"\n✅ Daily ingestion completed successfully.")
            print(f"   Chunks indexed: {result.get('chunks_indexed', 0)}")
            print(f"   Duration: {result.get('duration_seconds', 0)}s")
        else:
            print(f"\n❌ Daily ingestion failed: {result.get('reason', 'unknown')}")
            sys.exit(1)
    else:
        start_scheduler()
