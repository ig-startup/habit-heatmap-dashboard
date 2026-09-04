"""Sync real GitHub contribution activity into the GitHub metric."""
import logging

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app import crud
from app.models import Metric
from app.schemas import MetricEventCreate
from app.services.github import fetch_contributions

logger = logging.getLogger(__name__)


async def _get_or_create_github_metric(session: AsyncSession, login: str) -> Metric:
    result = await session.execute(select(Metric).where(Metric.source_type == "github"))
    metric = result.scalars().first()
    if metric:
        return metric

    metric = Metric(
        name=f"GitHub — {login}",
        icon="🐙",
        color="#3fb950",
        unit="count",
        aggregation="sum",
        source_type="github",
        meta={"login": login, "mock": False},
    )
    session.add(metric)
    await session.flush()
    return metric


async def sync_github_metric(session: AsyncSession, login: str, token: str) -> None:
    metric = await _get_or_create_github_metric(session, login)
    contributions = await fetch_contributions(login, token)
    for day, count in contributions:
        await crud.upsert_event(session, metric.id, MetricEventCreate(date=day, value=count, meta={}))
    logger.info("Synced %d days of GitHub activity for %s", len(contributions), login)
