"""GitHub GraphQL client — fetches the public contribution calendar for a user."""
from datetime import date, datetime

import httpx

GRAPHQL_URL = "https://api.github.com/graphql"

_CONTRIBUTIONS_QUERY = """
query($login: String!) {
  user(login: $login) {
    contributionsCollection {
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


async def fetch_contributions(login: str, token: str) -> list[tuple[date, int]]:
    """Fetch the last ~12 months of daily contribution counts for a GitHub user."""
    async with httpx.AsyncClient(timeout=15) as client:
        response = await client.post(
            GRAPHQL_URL,
            json={"query": _CONTRIBUTIONS_QUERY, "variables": {"login": login}},
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
