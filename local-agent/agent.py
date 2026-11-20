"""Local agent daemon — collects Obsidian + YouTube + Telegram activity and pushes it to the backend.

Meant to run periodically (see launchd/agent.plist): every 30 minutes and whenever
the network changes. Collected values go to a durable outbox (state/outbox.json)
and are re-sent on later runs until the backend accepts them, so a run without
network delays data instead of losing it.
Configuration is read from the repo-root .env: BACKEND_URL, INGEST_TOKEN,
OBSIDIAN_ARTICLES_PATH, TELEGRAM_CHANNEL.

Telegram only picks up the most recent ~20 posts each run (see
collectors/telegram.py) — for older history, run backfill_telegram.py once.
"""
from __future__ import annotations

import logging
import os
from datetime import date
from pathlib import Path

import httpx
from dotenv import load_dotenv

from collectors.obsidian import collect_words_written_today
from collectors.telegram import collect_recent_post_counts
from collectors.youtube import collect_youtube_seconds_today
from outbox import Outbox

ROOT = Path(__file__).resolve().parent.parent
load_dotenv(ROOT / ".env")

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")
logger = logging.getLogger(__name__)

BACKEND_URL = os.getenv("BACKEND_URL", "http://localhost:8000")
INGEST_TOKEN = os.getenv("INGEST_TOKEN")
OBSIDIAN_ARTICLES_PATH = os.getenv("OBSIDIAN_ARTICLES_PATH", "")
# Off by default: reading knowledgeC.db needs Full Disk Access, a broad TCC grant
# to the whole python3 binary (not just this script) — deferred pending a safer
# setup (dedicated interpreter). See local-agent/README.md.
YOUTUBE_COLLECTOR_ENABLED = os.getenv("YOUTUBE_COLLECTOR_ENABLED", "false").lower() == "true"
TELEGRAM_CHANNEL = os.getenv("TELEGRAM_CHANNEL", "")
STATE_PATH = Path(__file__).resolve().parent / "state" / "obsidian.json"
# Values are queued here first and removed only after the backend confirms them.
OUTBOX_PATH = Path(__file__).resolve().parent / "state" / "outbox.json"
FLUSH_RETRIES = 4
FLUSH_RETRY_DELAY_SECONDS = 30


def _send(slug: str, day: str, value: float) -> None:
    """Push one value to the backend; raises on any failure (network, 5xx, auth)."""
    response = httpx.post(
        f"{BACKEND_URL}/api/metrics/{slug}/ingest",
        json={"date": day, "value": value},
        headers={"X-Ingest-Token": INGEST_TOKEN},
        timeout=10,
    )
    response.raise_for_status()
    logger.info("%s: ingested value=%s date=%s", slug, value, day)


def run_once() -> None:
    outbox = Outbox(OUTBOX_PATH)

    vault_path = Path(OBSIDIAN_ARTICLES_PATH) if OBSIDIAN_ARTICLES_PATH else None
    if vault_path and vault_path.exists():
        words = collect_words_written_today(vault_path, STATE_PATH)
        outbox.put("obsidian", date.today().isoformat(), words)
    else:
        logger.error("OBSIDIAN_ARTICLES_PATH not set or missing: %s", OBSIDIAN_ARTICLES_PATH)

    if not YOUTUBE_COLLECTOR_ENABLED:
        logger.info("YouTube collector disabled (YOUTUBE_COLLECTOR_ENABLED=false) — skipping")
    else:
        try:
            seconds = collect_youtube_seconds_today()
            outbox.put("youtube", date.today().isoformat(), round(seconds / 60, 1))
        except Exception:
            logger.exception("YouTube collector failed — is Full Disk Access granted to this Python?")

    if not TELEGRAM_CHANNEL:
        logger.info("TELEGRAM_CHANNEL not set — skipping Telegram collector")
    else:
        try:
            counts = collect_recent_post_counts(TELEGRAM_CHANNEL)
            for day_str, count in counts.items():
                outbox.put("telegram", day_str, count)
        except Exception:
            logger.exception("Telegram collector failed")

    if not INGEST_TOKEN:
        logger.error("INGEST_TOKEN not set — values stay in the outbox until it is")
        return
    # Right after wake-up the network may need a minute — retry a few times before giving up.
    outbox.flush(_send, retries=FLUSH_RETRIES, retry_delay=FLUSH_RETRY_DELAY_SECONDS)


if __name__ == "__main__":
    run_once()
