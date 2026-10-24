from datetime import date, timedelta

import pytest

from app.api import competition
from app.scoring import GITHUB_PARAMS, OBSIDIAN_PARAMS, daily_points, week_start

TOKEN = "test-ingest-token"


@pytest.fixture(autouse=True)
def challenge_started_three_weeks_ago(monkeypatch):
    monkeypatch.setattr(competition, "CHALLENGE_START", week_start(date.today()) - timedelta(weeks=3))


def _start() -> date:
    return competition.CHALLENGE_START


@pytest.mark.asyncio
async def test_no_metrics_returns_zeroed_players(client):
    resp = await client.get("/api/competition")
    assert resp.status_code == 200
    body = resp.json()
    assert body["start_date"] == _start().isoformat()
    assert body["weeks"] == 12
    assert {p["id"] for p in body["players"]} == {"brat", "ty"}
    for player in body["players"]:
        assert player["metric_found"] is False
        assert player["cumulative_points"] == 0
        assert player["daily"] == []
        assert len(player["weekly"]) == 12
        assert all(w["points_total"] == 0 for w in player["weekly"])


@pytest.mark.asyncio
async def test_cumulative_points_match_formula(client):
    resp = await client.post("/api/metrics", json={"name": "GitHub", "source_type": "github"})
    metric_id = resp.json()["id"]
    start = _start()

    github_values = [1, 3, 6]  # 1 is at threshold -> contributes 0 points
    for offset, value in enumerate(github_values):
        await client.post(
            f"/api/metrics/{metric_id}/events",
            json={"date": (start + timedelta(days=offset)).isoformat(), "value": value},
        )

    obsidian_values = [80, 300, 600]  # 80 is at threshold -> contributes 0 points
    for offset, value in enumerate(obsidian_values):
        await client.post(
            "/api/metrics/obsidian/ingest",
            json={"date": (start + timedelta(days=offset)).isoformat(), "value": value},
            headers={"X-Ingest-Token": TOKEN},
        )

    body = (await client.get("/api/competition")).json()
    players = {p["id"]: p for p in body["players"]}

    assert players["brat"]["metric_found"] is True
    assert players["brat"]["cumulative_points"] == pytest.approx(
        sum(daily_points(v, GITHUB_PARAMS) for v in github_values)
    )
    assert players["ty"]["metric_found"] is True
    assert players["ty"]["cumulative_points"] == pytest.approx(
        sum(daily_points(v, OBSIDIAN_PARAMS) for v in obsidian_values)
    )


@pytest.mark.asyncio
async def test_weekly_window_starts_at_challenge_start_and_ascends(client):
    resp = await client.post("/api/metrics", json={"name": "GitHub", "source_type": "github"})
    metric_id = resp.json()["id"]
    start = _start()

    await client.post(
        f"/api/metrics/{metric_id}/events", json={"date": start.isoformat(), "value": 6}
    )
    await client.post(
        f"/api/metrics/{metric_id}/events",
        json={"date": (start + timedelta(weeks=2)).isoformat(), "value": 6},
    )

    body = (await client.get("/api/competition")).json()
    brat = next(p for p in body["players"] if p["id"] == "brat")
    weeks = [w["week_start"] for w in brat["weekly"]]

    assert len(weeks) == 12
    assert weeks[0] == start.isoformat()
    assert weeks == sorted(weeks)
    assert brat["weekly"][0]["points_total"] > 0
    assert brat["weekly"][1]["points_total"] == 0
    assert brat["weekly"][2]["points_total"] > 0


@pytest.mark.asyncio
async def test_events_before_challenge_start_are_ignored(client):
    resp = await client.post("/api/metrics", json={"name": "GitHub", "source_type": "github"})
    metric_id = resp.json()["id"]
    start = _start()

    await client.post(
        f"/api/metrics/{metric_id}/events",
        json={"date": (start - timedelta(days=1)).isoformat(), "value": 12},
    )
    await client.post(
        f"/api/metrics/{metric_id}/events", json={"date": start.isoformat(), "value": 6}
    )

    body = (await client.get("/api/competition")).json()
    brat = next(p for p in body["players"] if p["id"] == "brat")
    assert [d["date"] for d in brat["daily"]] == [start.isoformat()]
    assert brat["cumulative_points"] == pytest.approx(daily_points(6, GITHUB_PARAMS))
