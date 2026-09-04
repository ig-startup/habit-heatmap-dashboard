from datetime import date

import pytest

TOKEN = "test-ingest-token"


@pytest.mark.asyncio
async def test_ingest_rejects_missing_token(client):
    resp = await client.post(
        "/api/metrics/obsidian/ingest", json={"date": date.today().isoformat(), "value": 120}
    )
    assert resp.status_code == 401


@pytest.mark.asyncio
async def test_ingest_rejects_wrong_token(client):
    resp = await client.post(
        "/api/metrics/obsidian/ingest",
        json={"date": date.today().isoformat(), "value": 120},
        headers={"X-Ingest-Token": "wrong"},
    )
    assert resp.status_code == 401


@pytest.mark.asyncio
async def test_ingest_unknown_slug_404(client):
    resp = await client.post(
        "/api/metrics/unknown/ingest",
        json={"date": date.today().isoformat(), "value": 1},
        headers={"X-Ingest-Token": TOKEN},
    )
    assert resp.status_code == 404


@pytest.mark.asyncio
async def test_ingest_creates_metric_lazily_and_upserts(client):
    today = date.today().isoformat()
    resp = await client.post(
        "/api/metrics/obsidian/ingest",
        json={"date": today, "value": 350},
        headers={"X-Ingest-Token": TOKEN},
    )
    assert resp.status_code == 201
    assert resp.json()["value"] == 350.0

    metrics = (await client.get("/api/metrics")).json()
    assert len(metrics) == 1
    assert metrics[0]["name"] == "Статьи в Obsidian"
    assert metrics[0]["today_value"] == 350.0

    # second ingest for the same day replaces the value (agent re-sends the day's running total)
    resp = await client.post(
        "/api/metrics/obsidian/ingest",
        json={"date": today, "value": 500},
        headers={"X-Ingest-Token": TOKEN},
    )
    assert resp.status_code == 201
    metrics = (await client.get("/api/metrics")).json()
    assert len(metrics) == 1
    assert metrics[0]["today_value"] == 500.0


@pytest.mark.asyncio
async def test_ingest_youtube_and_obsidian_are_separate_metrics(client):
    today = date.today().isoformat()
    await client.post(
        "/api/metrics/obsidian/ingest",
        json={"date": today, "value": 10},
        headers={"X-Ingest-Token": TOKEN},
    )
    await client.post(
        "/api/metrics/youtube/ingest",
        json={"date": today, "value": 42},
        headers={"X-Ingest-Token": TOKEN},
    )
    metrics = (await client.get("/api/metrics")).json()
    assert {m["name"] for m in metrics} == {"Статьи в Obsidian", "YouTube"}
