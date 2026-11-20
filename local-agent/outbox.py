"""Durable outbox: values to push to the backend survive failed sends.

Each collected value is first written to disk (`put`), then `flush` tries to send
everything that the backend hasn't confirmed yet. A value stays queued until a
send succeeds, so a run without network (e.g. right after the Mac wakes up) only
delays the data instead of losing it. Re-sending is safe: the backend ingest
upserts by date. Values already confirmed with the same number are not re-sent
(`sent` keeps one number per metric per day — never pruned, it stays tiny, and
pruning would make old days still visible to a collector get re-sent every run).
"""
from __future__ import annotations

import json
import logging
import time
from pathlib import Path
from typing import Callable

logger = logging.getLogger(__name__)


class Outbox:
    def __init__(self, path: Path):
        self.path = path
        data = json.loads(path.read_text()) if path.exists() else {}
        self.pending: dict[str, dict[str, float]] = data.get("pending", {})
        self.sent: dict[str, dict[str, float]] = data.get("sent", {})

    def put(self, slug: str, day: str, value: float) -> None:
        if self.sent.get(slug, {}).get(day) == value:
            return  # backend already has exactly this value
        self.pending.setdefault(slug, {})[day] = value
        self._save()

    def flush(
        self,
        send: Callable[[str, str, float], None],
        retries: int = 0,
        retry_delay: float = 0,
        sleep: Callable[[float], None] = time.sleep,
    ) -> int:
        """Send all pending values; returns how many are still pending.

        `send(slug, day, value)` must raise on failure. On failure the whole
        flush is retried up to `retries` times (network may come up a bit later).
        """
        for attempt in range(retries + 1):
            failed = False
            for slug in list(self.pending):
                for day, value in sorted(self.pending[slug].items()):
                    try:
                        send(slug, day, value)
                    except Exception:
                        logger.exception("%s: send failed for %s (kept in outbox)", slug, day)
                        failed = True
                        break  # backend/network is down — no point trying the rest now
                    del self.pending[slug][day]
                    self.sent.setdefault(slug, {})[day] = value
                    self._save()
                if not self.pending.get(slug):
                    self.pending.pop(slug, None)
                if failed:
                    break
            if not failed:
                break
            if attempt < retries:
                logger.info("Outbox: retrying in %ss (%d/%d)", retry_delay, attempt + 1, retries)
                sleep(retry_delay)

        self._save()
        left = sum(len(days) for days in self.pending.values())
        if left:
            logger.warning("Outbox: %d value(s) still pending, will retry next run", left)
        return left

    def _save(self) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        tmp = self.path.with_suffix(".tmp")
        tmp.write_text(json.dumps({"pending": self.pending, "sent": self.sent}, ensure_ascii=False))
        tmp.replace(self.path)
