"""Seed a realistic mock GitHub activity metric on first boot (MVP — real API comes later)."""
import logging
import random
from datetime import date, timedelta

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import Metric, MetricEvent

logger = logging.getLogger(__name__)


async def seed_if_empty(session: AsyncSession) -> None:
    existing = await session.execute(select(Metric).limit(1))
    if existing.scalar_one_or_none():
        return

    metric = Metric(
        name="GitHub — я",
        icon="🐙",
        color="#3fb950",
        unit="count",
        aggregation="sum",
        source_type="github",
        meta={"login": "me", "mock": True},
    )
    session.add(metric)
    await session.flush()

    rng = random.Random(42)
    today = date.today()
    for offset in range(365, -1, -1):
        day = today - timedelta(days=offset)
        is_weekend = day.weekday() >= 5
        # ~20% полностью пустых дней, выходные — заметно тише будних
        if rng.random() < (0.35 if is_weekend else 0.12):
            continue
        base = rng.randint(1, 4) if is_weekend else rng.randint(1, 12)
        session.add(MetricEvent(metric_id=metric.id, date=day, value=base))

    await session.commit()
    logger.info("Seeded mock GitHub metric with 1 year of activity")
