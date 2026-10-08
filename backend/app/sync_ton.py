"""Sync the current TON wallet balance into a daily-snapshot metric.

Unlike GitHub/Metrika, the public TON API only exposes the *current* balance, not
history — so each sync just upserts today's date with the latest reading. Past
days before tracking started stay blank, same as any other metric added mid-year.
"""
import logging
from datetime import date

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app import crud
from app.models import Metric
from app.schemas import MetricEventCreate
from app.services.ton import fetch_balance

logger = logging.getLogger(__name__)


async def _get_or_create_ton_metric(session: AsyncSession, address: str) -> Metric:
    result = await session.execute(select(Metric).where(Metric.source_type == "ton"))
    metric = result.scalars().first()
    if metric:
        return metric

    metric = Metric(
        name="TON-кошелёк",
        icon="💎",
        color="#0098ea",
        unit="count",
        aggregation="last",
        source_type="ton",
        meta={"address": address},
    )
    session.add(metric)
    await session.flush()
    return metric


async def sync_ton_metric(session: AsyncSession, address: str) -> None:
    metric = await _get_or_create_ton_metric(session, address)
    balance = await fetch_balance(address)
    await crud.upsert_event(
        session, metric.id, MetricEventCreate(date=date.today(), value=round(balance, 4), meta={})
    )
    logger.info("Synced TON balance for %s: %.4f TON", address, balance)
