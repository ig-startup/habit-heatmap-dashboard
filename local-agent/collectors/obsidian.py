"""Obsidian word-count collector — see ТЗ §2.2."""
import json
import logging
from datetime import date
from pathlib import Path

logger = logging.getLogger(__name__)


def _word_count(path: Path) -> int:
    try:
        return len(path.read_text(encoding="utf-8", errors="ignore").split())
    except OSError:
        return 0


def _current_counts(vault_path: Path) -> dict[str, int]:
    return {str(p.relative_to(vault_path)): _word_count(p) for p in vault_path.rglob("*.md")}


def collect_words_written_today(vault_path: Path, state_path: Path) -> int:
    """Return the running total of words written today under `vault_path`.

    Each run diffs current per-file word counts against the snapshot saved by the
    *previous* run and adds the positive deltas to today's total (persisted in
    `state_path`), then saves the new snapshot. The total resets when the day rolls
    over, but the snapshot does not: words typed while the Mac was asleep (e.g.
    overnight) are counted on the first run afterwards instead of being swallowed
    into a fresh baseline. Only positive deltas count, so an edit that shrinks a
    file doesn't subtract — a deliberately rough metric (see ТЗ §2.2).
    """
    today = date.today().isoformat()
    state = json.loads(state_path.read_text()) if state_path.exists() else {}

    current = _current_counts(vault_path)

    # "baseline_counts" is the pre-rolling-snapshot state format; first run ever diffs against itself.
    previous = state.get("last_counts")
    if previous is None:
        previous = state.get("baseline_counts", current)
    delta = sum(max(0, count - previous.get(relpath, 0)) for relpath, count in current.items())

    total = state.get("total", 0) if state.get("date") == today else 0
    total += delta

    state_path.parent.mkdir(parents=True, exist_ok=True)
    state_path.write_text(json.dumps({"date": today, "total": total, "last_counts": current}))

    logger.info("Obsidian: %d words written today across %d files", total, len(current))
    return total
