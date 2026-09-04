from datetime import date
from unittest.mock import AsyncMock, patch

import pytest
from sqlalchemy import select

from app.db import Base, async_session, engine
from app.models import Metric, MetricEvent
from app.services.github import fetch_contributions
from app.sync_github import sync_github_metric


class _FakeResponse:
    def __init__(self, payload):
        self._payload = payload

    def raise_for_status(self):
        pass

    def json(self):
        return self._payload


@pytest.mark.asyncio
async def test_fetch_contributions_parses_calendar():
    payload = {
        "data": {
            "user": {
                "contributionsCollection": {
                    "contributionCalendar": {
                        "weeks": [
                            {
                                "contributionDays": [
                                    {"date": "2026-01-01", "contributionCount": 3},
                                    {"date": "2026-01-02", "contributionCount": 0},
                                ]
                            }
                        ]
                    }
                }
            }
        }
    }
    with patch("httpx.AsyncClient.post", new=AsyncMock(return_value=_FakeResponse(payload))):
        result = await fetch_contributions("IGfinance", "fake-token")

    assert result == [(date(2026, 1, 1), 3), (date(2026, 1, 2), 0)]


@pytest.mark.asyncio
async def test_fetch_contributions_raises_on_missing_user():
    payload = {"data": {"user": None}}
    with patch("httpx.AsyncClient.post", new=AsyncMock(return_value=_FakeResponse(payload))):
        with pytest.raises(RuntimeError):
            await fetch_contributions("ghost", "fake-token")


@pytest.mark.asyncio
async def test_sync_github_metric_upserts_events():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    contributions = [(date(2026, 1, 1), 3), (date(2026, 1, 2), 0)]
    try:
        async with async_session() as session:
            with patch("app.sync_github.fetch_contributions", new=AsyncMock(return_value=contributions)):
                await sync_github_metric(session, "IGfinance", "fake-token")

            metrics = (await session.execute(select(Metric))).scalars().all()
            assert len(metrics) == 1
            assert metrics[0].meta == {"login": "IGfinance", "mock": False}

            events = (await session.execute(select(MetricEvent))).scalars().all()
            assert {(e.date, float(e.value)) for e in events} == {
                (date(2026, 1, 1), 3.0),
                (date(2026, 1, 2), 0.0),
            }
    finally:
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.drop_all)
