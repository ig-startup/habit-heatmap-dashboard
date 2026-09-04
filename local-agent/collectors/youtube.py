"""macOS Screen Time (knowledgeC.db) YouTube-usage collector — see ТЗ §2.3.

Reads the same SQLite database System Settings → Screen Time is built on.
The schema is undocumented by Apple but long reverse-engineered by the
community: ZOBJECT rows carry ZSTARTDATE/ZENDDATE (Core Data timestamps —
seconds since 2001-01-01, not Unix epoch) and ZVALUESTRING, which holds
either an app bundle id (e.g. com.google.Chrome) or, for browser tab
activity, the visited domain. We don't rely on a specific ZSTREAMNAME
because it varies across macOS versions — instead we match any row whose
ZVALUESTRING mentions "youtube".

Requires Full Disk Access for the Python interpreter running this script:
System Settings → Privacy & Security → Full Disk Access. Without it,
sqlite3 raises "unable to open database file".
"""
import logging
import sqlite3
from datetime import date, datetime, timedelta
from pathlib import Path

logger = logging.getLogger(__name__)

CORE_DATA_EPOCH_OFFSET = 978307200  # seconds between 1970-01-01 and 2001-01-01
DEFAULT_DB_PATH = Path.home() / "Library/Application Support/Knowledge/knowledgeC.db"


def _to_core_data_ts(dt: datetime) -> float:
    return dt.timestamp() - CORE_DATA_EPOCH_OFFSET


def collect_youtube_seconds_today(db_path: Path = DEFAULT_DB_PATH) -> int:
    """Sum seconds of YouTube usage (app or website) recorded today in Screen Time."""
    today = date.today()
    day_start = _to_core_data_ts(datetime.combine(today, datetime.min.time()))
    day_end = _to_core_data_ts(datetime.combine(today + timedelta(days=1), datetime.min.time()))

    conn = sqlite3.connect(f"file:{db_path}?mode=ro", uri=True)
    try:
        rows = conn.execute(
            """
            SELECT ZSTARTDATE, ZENDDATE
            FROM ZOBJECT
            WHERE ZSTARTDATE >= ? AND ZSTARTDATE < ?
              AND ZVALUESTRING IS NOT NULL
              AND LOWER(ZVALUESTRING) LIKE '%youtube%'
            """,
            (day_start, day_end),
        ).fetchall()
    finally:
        conn.close()

    total_seconds = sum(max(0.0, (end or start) - start) for start, end in rows)
    logger.info("YouTube: %.0f seconds across %d Screen Time entries today", total_seconds, len(rows))
    return int(total_seconds)
