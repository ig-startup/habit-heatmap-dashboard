"""Queries and derived stats (streak / total days / today's value)."""
from datetime import date, timedelta

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import Metric, MetricEvent
from app.schemas import MetricCreate, MetricEventCreate


async def list_metrics(session: AsyncSession) -> list[Metric]:
    result = await session.execute(select(Metric).order_by(Metric.created_at))
    return list(result.scalars().all())


async def create_metric(session: AsyncSession, data: MetricCreate) -> Metric:
    metric = Metric(**data.model_dump())
    session.add(metric)
    await session.commit()
    await session.refresh(metric)
    return metric


async def get_metric(session: AsyncSession, metric_id: int) -> Metric | None:
    return await session.get(Metric, metric_id)


async def get_or_create_metric_by_slug(session: AsyncSession, slug: str, defaults: dict) -> Metric:
    """Find a webhook-sourced metric by its meta.slug, creating it on first ingest."""
    result = await session.execute(select(Metric).where(Metric.source_type == "webhook"))
    for metric in result.scalars().all():
        if metric.meta.get("slug") == slug:
            return metric

    metric = Metric(source_type="webhook", meta={"slug": slug}, **defaults)
    session.add(metric)
    await session.commit()
    await session.refresh(metric)
    return metric


async def upsert_event(session: AsyncSession, metric_id: int, data: MetricEventCreate) -> MetricEvent:
    result = await session.execute(
        select(MetricEvent).where(MetricEvent.metric_id == metric_id, MetricEvent.date == data.date)
    )
    event = result.scalar_one_or_none()
    if event:
        event.value = data.value
        event.meta = data.meta
    else:
        event = MetricEvent(metric_id=metric_id, date=data.date, value=data.value, meta=data.meta)
        session.add(event)
    await session.commit()
    await session.refresh(event)
    return event


async def events_for_year(session: AsyncSession, metric_id: int, year: int) -> list[MetricEvent]:
    result = await session.execute(
        select(MetricEvent)
        .where(
            MetricEvent.metric_id == metric_id,
            MetricEvent.date >= date(year, 1, 1),
            MetricEvent.date <= date(year, 12, 31),
        )
        .order_by(MetricEvent.date)
    )
    return list(result.scalars().all())


async def compute_stats(session: AsyncSession, metric_id: int, today: date | None = None) -> dict:
    """streak (consecutive tracked days ending today/yesterday), total tracked days, today's value."""
    today = today or date.today()
    result = await session.execute(
        select(MetricEvent.date, MetricEvent.value)
        .where(MetricEvent.metric_id == metric_id, MetricEvent.value > 0)
    )
    tracked_dates = {row.date for row in result.all()}

    total_days_tracked = len(tracked_dates)

    anchor = today if today in tracked_dates else today - timedelta(days=1)
    streak = 0
    cursor = anchor
    while cursor in tracked_dates:
        streak += 1
        cursor -= timedelta(days=1)

    today_result = await session.execute(
        select(MetricEvent.value).where(MetricEvent.metric_id == metric_id, MetricEvent.date == today)
    )
    today_value = today_result.scalar_one_or_none()

    return {
        "streak": streak,
        "total_days_tracked": total_days_tracked,
        "today_value": float(today_value) if today_value is not None else None,
    }
