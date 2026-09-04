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

    Compares current per-file word counts against a baseline snapshot taken at
    the first run of the day (persisted in `state_path`); the baseline resets
    whenever the day rolls over. Only positive deltas count, so an edit that
    shrinks a file doesn't subtract from the day's total — a deliberately
    rough metric (see ТЗ §2.2), not an accurate diff.
    """
    today = date.today().isoformat()
    state = json.loads(state_path.read_text()) if state_path.exists() else {}

    current = _current_counts(vault_path)

    if state.get("baseline_date") != today:
        state = {"baseline_date": today, "baseline_counts": current}

    baseline = state["baseline_counts"]
    words_written = sum(max(0, count - baseline.get(relpath, 0)) for relpath, count in current.items())

    state_path.parent.mkdir(parents=True, exist_ok=True)
    state_path.write_text(json.dumps(state))

    logger.info("Obsidian: %d words written today across %d files", words_written, len(current))
    return words_written
