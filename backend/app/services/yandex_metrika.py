"""Yandex Metrika Reporting API client — fetches daily visits for a counter."""
from datetime import date, timedelta

import httpx

STAT_URL = "https://api-metrika.yandex.net/stat/v1/data"


async def fetch_visits(
    counter_id: str, token: str, from_date: date | None = None, to_date: date | None = None
) -> list[tuple[date, int]]:
    """Fetch daily visit counts for a Metrika counter between from_date and to_date (inclusive).

    Defaults to January 1st of the current year through today.
    """
    today = date.today()
    from_date = from_date or date(today.year, 1, 1)
    to_date = to_date or today

    params = {
        "ids": counter_id,
        "metrics": "ym:s:visits",
        "dimensions": "ym:s:date",
        "date1": from_date.isoformat(),
        "date2": to_date.isoformat(),
        "limit": 10000,
    }

    async with httpx.AsyncClient(timeout=15) as client:
        response = await client.get(
            STAT_URL,
            params=params,
            headers={"Authorization": f"OAuth {token}"},
        )
        response.raise_for_status()
        payload = response.json()

    rows = payload.get("data", [])
    result: list[tuple[date, int]] = []
    for row in rows:
        day_str = row["dimensions"][0]["name"]
        visits = int(row["metrics"][0])
        result.append((date.fromisoformat(day_str), visits))
    result.sort(key=lambda item: item[0])

    seen = {day: count for day, count in result}
    cursor = from_date
    filled: list[tuple[date, int]] = []
    while cursor <= to_date:
        filled.append((cursor, seen.get(cursor, 0)))
        cursor += timedelta(days=1)
    return filled
