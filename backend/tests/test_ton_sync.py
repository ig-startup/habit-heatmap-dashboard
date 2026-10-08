from datetime import date
from unittest.mock import AsyncMock, patch

import pytest
from sqlalchemy import select

from app.db import Base, async_session, engine
from app.models import Metric, MetricEvent
from app.services.ton import fetch_balance
from app.sync_ton import sync_ton_metric


class _FakeResponse:
    def __init__(self, payload):
        self._payload = payload

    def raise_for_status(self):
        pass

    def json(self):
        return self._payload


@pytest.mark.asyncio
async def test_fetch_balance_converts_nanotons():
    payload = {"ok": True, "result": "1500000000"}
    with patch("httpx.AsyncClient.get", new=AsyncMock(return_value=_FakeResponse(payload))):
        result = await fetch_balance("UQAfake")

    assert result == 1.5


@pytest.mark.asyncio
async def test_sync_ton_metric_upserts_today():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    try:
        async with async_session() as session:
            with patch("app.sync_ton.fetch_balance", new=AsyncMock(return_value=12.3456)):
                await sync_ton_metric(session, "UQAfake")

            metrics = (await session.execute(select(Metric))).scalars().all()
            assert len(metrics) == 1
            assert metrics[0].source_type == "ton"
            assert metrics[0].meta == {"address": "UQAfake"}

            events = (await session.execute(select(MetricEvent))).scalars().all()
            assert len(events) == 1
            assert events[0].date == date.today()
            assert float(events[0].value) == 12.3456
    finally:
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.drop_all)
