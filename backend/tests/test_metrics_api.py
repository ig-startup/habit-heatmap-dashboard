from datetime import date, timedelta

import pytest


@pytest.mark.asyncio
async def test_create_and_list_metric(client):
    resp = await client.post("/api/metrics", json={"name": "Отжимания", "unit": "count"})
    assert resp.status_code == 201
    body = resp.json()
    assert body["name"] == "Отжимания"
    assert body["streak"] == 0
    assert body["total_days_tracked"] == 0

    resp = await client.get("/api/metrics")
    assert resp.status_code == 200
    assert len(resp.json()) == 1


@pytest.mark.asyncio
async def test_streak_breaks_on_gap(client):
    resp = await client.post("/api/metrics", json={"name": "GitHub", "source_type": "github"})
    metric_id = resp.json()["id"]

    today = date.today()
    # tracked today, yesterday, day before — gap two days ago, then one more tracked day
    for offset in (0, 1, 2):
        await client.post(
            f"/api/metrics/{metric_id}/events",
            json={"date": (today - timedelta(days=offset)).isoformat(), "value": 3},
        )
    await client.post(
        f"/api/metrics/{metric_id}/events",
        json={"date": (today - timedelta(days=5)).isoformat(), "value": 3},
    )

    resp = await client.get("/api/metrics")
    stats = resp.json()[0]
    assert stats["streak"] == 3
    assert stats["total_days_tracked"] == 4
    assert stats["today_value"] == 3.0


@pytest.mark.asyncio
async def test_heatmap_year_scoped(client):
    resp = await client.post("/api/metrics", json={"name": "GitHub"})
    metric_id = resp.json()["id"]

    this_year = date.today().year
    await client.post(
        f"/api/metrics/{metric_id}/events",
        json={"date": f"{this_year}-01-15", "value": 5},
    )
    await client.post(
        f"/api/metrics/{metric_id}/events",
        json={"date": f"{this_year - 1}-06-01", "value": 5},
    )

    resp = await client.get(f"/api/metrics/{metric_id}/heatmap?year={this_year}")
    assert resp.status_code == 200
    events = resp.json()
    assert len(events) == 1
    assert events[0]["date"] == f"{this_year}-01-15"


@pytest.mark.asyncio
async def test_event_upsert_replaces_value(client):
    resp = await client.post("/api/metrics", json={"name": "GitHub"})
    metric_id = resp.json()["id"]
    today = date.today().isoformat()

    await client.post(f"/api/metrics/{metric_id}/events", json={"date": today, "value": 2})
    resp = await client.post(f"/api/metrics/{metric_id}/events", json={"date": today, "value": 9})
    assert resp.json()["value"] == 9.0

    resp = await client.get(f"/api/metrics/{metric_id}/heatmap?year={date.today().year}")
    assert len(resp.json()) == 1


@pytest.mark.asyncio
async def test_event_for_missing_metric_404(client):
    resp = await client.post("/api/metrics/999/events", json={"date": date.today().isoformat(), "value": 1})
    assert resp.status_code == 404
