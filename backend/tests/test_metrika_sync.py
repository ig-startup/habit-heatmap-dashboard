from datetime import date
from unittest.mock import AsyncMock, patch

import pytest
from sqlalchemy import select

from app.db import Base, async_session, engine
from app.models import Metric, MetricEvent
from app.services.yandex_metrika import fetch_visits
from app.sync_metrika import sync_metrika_metric


class _FakeResponse:
    def __init__(self, payload):
        self._payload = payload

    def raise_for_status(self):
        pass

    def json(self):
        return self._payload


@pytest.mark.asyncio
async def test_fetch_visits_parses_and_fills_gaps():
    payload = {
        "data": [
            {"dimensions": [{"name": "2026-01-01"}], "metrics": [12]},
            {"dimensions": [{"name": "2026-01-03"}], "metrics": [7]},
        ]
    }
    with patch("httpx.AsyncClient.get", new=AsyncMock(return_value=_FakeResponse(payload))):
        result = await fetch_visits(
            "12345", "fake-token", from_date=date(2026, 1, 1), to_date=date(2026, 1, 3)
        )

    assert result == [
        (date(2026, 1, 1), 12),
        (date(2026, 1, 2), 0),
        (date(2026, 1, 3), 7),
    ]


@pytest.mark.asyncio
async def test_sync_metrika_metric_upserts_events():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    visits = [(date(2026, 1, 1), 12), (date(2026, 1, 2), 0)]
    try:
        async with async_session() as session:
            with patch("app.sync_metrika.fetch_visits", new=AsyncMock(return_value=visits)):
                await sync_metrika_metric(session, "12345", "fake-token")

            metrics = (await session.execute(select(Metric))).scalars().all()
            assert len(metrics) == 1
            assert metrics[0].source_type == "metrika"
            assert metrics[0].meta == {"counter_id": "12345", "mock": False}

            events = (await session.execute(select(MetricEvent))).scalars().all()
            assert {(e.date, float(e.value)) for e in events} == {
                (date(2026, 1, 1), 12.0),
                (date(2026, 1, 2), 0.0),
            }
    finally:
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.drop_all)
