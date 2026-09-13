"""Sync real Yandex Metrika visit activity into the website-visitors metric."""
import logging

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app import crud
from app.models import Metric
from app.schemas import MetricEventCreate
from app.services.yandex_metrika import fetch_visits

logger = logging.getLogger(__name__)


async def _get_or_create_metrika_metric(session: AsyncSession, counter_id: str) -> Metric:
    result = await session.execute(select(Metric).where(Metric.source_type == "metrika"))
    metric = result.scalars().first()
    if metric:
        return metric

    metric = Metric(
        name="Посетители сайта",
        icon="📈",
        color="#ff7a30",
        unit="count",
        aggregation="sum",
        source_type="metrika",
        meta={"counter_id": counter_id, "mock": False},
    )
    session.add(metric)
    await session.flush()
    return metric


async def sync_metrika_metric(session: AsyncSession, counter_id: str, token: str) -> None:
    metric = await _get_or_create_metrika_metric(session, counter_id)
    visits = await fetch_visits(counter_id, token)
    for day, count in visits:
        await crud.upsert_event(session, metric.id, MetricEventCreate(date=day, value=count, meta={}))
    logger.info("Synced %d days of Yandex Metrika visits for counter %s", len(visits), counter_id)
