"""Telegram channel posts collector.

Scrapes the public `t.me/s/<channel>` preview page (no login, no API keys —
works for any public channel). Each message = 1 post, grouped by the UTC date
of its `datetime` attribute.
"""
from __future__ import annotations

import logging
import re
import time
from datetime import date, datetime, timezone

import httpx

logger = logging.getLogger(__name__)

_BASE_URL = "https://t.me/s/{channel}"
_POST_RE = re.compile(
    r'<a class="tgme_widget_message_date" href="https://t\.me/[^/"]+/(\d+)">'
    r'<time datetime="([^"]+)"'
)


def _fetch(channel: str, before: int | None, client: httpx.Client) -> str:
    params = {"before": before} if before else None
    response = client.get(
        _BASE_URL.format(channel=channel),
        params=params,
        headers={"User-Agent": "Mozilla/5.0"},
        timeout=15,
    )
    response.raise_for_status()
    return response.text


def _parse_posts(html: str) -> dict[int, date]:
    """Return {post_id: utc_date} for every message on a preview page."""
    posts = {}
    for post_id, iso_dt in _POST_RE.findall(html):
        dt = datetime.fromisoformat(iso_dt).astimezone(timezone.utc)
        posts[int(post_id)] = dt.date()
    return posts


def _counts_by_day(posts: dict[int, date]) -> dict[str, int]:
    counts: dict[str, int] = {}
    for day in posts.values():
        key = day.isoformat()
        counts[key] = counts.get(key, 0) + 1
    return counts


def collect_recent_post_counts(channel: str) -> dict[str, int]:
    """Post counts per day from the single most-recent preview page (~20 posts).

    Cheap enough to run every agent cycle; won't see posts older than the
    current page, so pair with `collect_full_history` for a one-off backfill.
    """
    with httpx.Client() as client:
        html = _fetch(channel, before=None, client=client)
    return _counts_by_day(_parse_posts(html))


def collect_full_history(channel: str, max_pages: int = 1000, delay_seconds: float = 0.3) -> dict[str, int]:
    """Walk `?before=` pagination back to the channel's first post, counting posts per day.

    Meant for a one-off backfill (see backfill_telegram.py) — safe to re-run,
    since the backend's ingest upserts by date rather than summing.
    """
    all_posts: dict[int, date] = {}
    before: int | None = None

    with httpx.Client() as client:
        for page in range(max_pages):
            html = _fetch(channel, before=before, client=client)
            page_posts = _parse_posts(html)
            if not page_posts:
                break
            all_posts.update(page_posts)
            oldest_id = min(page_posts)
            if before is not None and oldest_id >= before:
                break  # no progress — avoid looping forever
            before = oldest_id
            if page + 1 < max_pages:
                time.sleep(delay_seconds)

    logger.info("Telegram: backfilled %d posts for @%s", len(all_posts), channel)
    return _counts_by_day(all_posts)
