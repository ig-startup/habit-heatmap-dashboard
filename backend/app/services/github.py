"""GitHub GraphQL client — fetches the public contribution calendar for a user."""
from datetime import date, datetime, timezone

import httpx

GRAPHQL_URL = "https://api.github.com/graphql"

_CONTRIBUTIONS_QUERY = """
query($login: String!, $from: DateTime!, $to: DateTime!) {
  user(login: $login) {
    contributionsCollection(from: $from, to: $to) {
      contributionCalendar {
        weeks {
          contributionDays {
            date
            contributionCount
          }
        }
      }
    }
  }
}
"""


async def fetch_contributions(
    login: str, token: str, from_date: date | None = None, to_date: date | None = None
) -> list[tuple[date, int]]:
    """Fetch daily contribution counts for a GitHub user between from_date and to_date (inclusive).

    Defaults to January 1st of the current year through today — the GraphQL API caps a single
    contributionsCollection window at 1 year, so callers wanting more history must page by year.
    """
    today = datetime.now(timezone.utc).date()
    from_date = from_date or date(today.year, 1, 1)
    to_date = to_date or today

    variables = {
        "login": login,
        "from": datetime.combine(from_date, datetime.min.time(), tzinfo=timezone.utc).isoformat(),
        "to": datetime.combine(to_date, datetime.max.time().replace(microsecond=0), tzinfo=timezone.utc).isoformat(),
    }

    async with httpx.AsyncClient(timeout=15) as client:
        response = await client.post(
            GRAPHQL_URL,
            json={"query": _CONTRIBUTIONS_QUERY, "variables": variables},
            headers={"Authorization": f"Bearer {token}"},
        )
        response.raise_for_status()
        payload = response.json()

    if payload.get("errors"):
        raise RuntimeError(f"GitHub GraphQL error: {payload['errors']}")

    user = payload["data"]["user"]
    if user is None:
        raise RuntimeError(f"GitHub user not found: {login}")

    weeks = user["contributionsCollection"]["contributionCalendar"]["weeks"]
    return [
        (datetime.strptime(day["date"], "%Y-%m-%d").date(), day["contributionCount"])
        for week in weeks
        for day in week["contributionDays"]
    ]
