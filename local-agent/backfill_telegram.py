"""One-off backfill: walks the full t.me/s/<channel> history and ingests post counts per day.

Run manually once (safe to re-run — the backend's ingest upserts by date,
it doesn't sum):

    .venv/bin/python3 backfill_telegram.py

Configuration from the repo-root .env: BACKEND_URL, INGEST_TOKEN, TELEGRAM_CHANNEL.
"""
import logging
import os
from pathlib import Path

import httpx
from dotenv import load_dotenv

from collectors.telegram import collect_full_history

ROOT = Path(__file__).resolve().parent.parent
load_dotenv(ROOT / ".env")

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")
logger = logging.getLogger(__name__)

BACKEND_URL = os.getenv("BACKEND_URL", "http://localhost:8000")
INGEST_TOKEN = os.getenv("INGEST_TOKEN")
TELEGRAM_CHANNEL = os.getenv("TELEGRAM_CHANNEL", "")


def main() -> None:
    if not TELEGRAM_CHANNEL:
        logger.error("TELEGRAM_CHANNEL not set")
        return
    if not INGEST_TOKEN:
        logger.error("INGEST_TOKEN not set")
        return

    counts = collect_full_history(TELEGRAM_CHANNEL)
    logger.info("Ingesting %d days of history for @%s", len(counts), TELEGRAM_CHANNEL)

    with httpx.Client() as client:
        for day_str, count in counts.items():
            response = client.post(
                f"{BACKEND_URL}/api/metrics/telegram/ingest",
                json={"date": day_str, "value": count},
                headers={"X-Ingest-Token": INGEST_TOKEN},
                timeout=10,
            )
            response.raise_for_status()

    logger.info("Backfill done")


if __name__ == "__main__":
    main()
