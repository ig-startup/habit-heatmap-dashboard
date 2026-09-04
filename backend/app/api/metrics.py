"""Router: /api/metrics"""
import hmac
import os
from datetime import date

from fastapi import APIRouter, Depends, Header, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app import crud
from app.db import get_session
from app.schemas import MetricCreate, MetricEventCreate, MetricEventOut, MetricIngest, MetricWithStats

router = APIRouter(prefix="/api/metrics", tags=["metrics"])

# Local-agent ingest sources (see ТЗ §2.2/2.3) — metrics are created lazily on first ingest.
INGEST_METRIC_DEFAULTS = {
    "obsidian": {"name": "Статьи в Obsidian", "icon": "📝", "color": "#a970ff", "unit": "count", "aggregation": "sum"},
    "youtube": {"name": "YouTube", "icon": "📺", "color": "#ff4d4f", "unit": "duration", "aggregation": "sum"},
}


def _verify_ingest_token(x_ingest_token: str | None) -> None:
    expected = os.getenv("INGEST_TOKEN")
    if not expected or not x_ingest_token or not hmac.compare_digest(x_ingest_token, expected):
        raise HTTPException(status_code=401, detail="Invalid or missing ingest token")


@router.get("", response_model=list[MetricWithStats])
async def get_metrics(session: AsyncSession = Depends(get_session)):
    metrics = await crud.list_metrics(session)
    out = []
    for metric in metrics:
        stats = await crud.compute_stats(session, metric.id)
        out.append(MetricWithStats.model_validate(metric).model_copy(update=stats))
    return out


@router.post("", response_model=MetricWithStats, status_code=201)
async def post_metric(body: MetricCreate, session: AsyncSession = Depends(get_session)):
    metric = await crud.create_metric(session, body)
    stats = await crud.compute_stats(session, metric.id)
    return MetricWithStats.model_validate(metric).model_copy(update=stats)


@router.get("/{metric_id}/heatmap", response_model=list[MetricEventOut])
async def get_heatmap(metric_id: int, year: int = date.today().year, session: AsyncSession = Depends(get_session)):
    metric = await crud.get_metric(session, metric_id)
    if not metric:
        raise HTTPException(status_code=404, detail="Metric not found")
    return await crud.events_for_year(session, metric_id, year)


@router.post("/{metric_id}/events", response_model=MetricEventOut, status_code=201)
async def post_event(metric_id: int, body: MetricEventCreate, session: AsyncSession = Depends(get_session)):
    metric = await crud.get_metric(session, metric_id)
    if not metric:
        raise HTTPException(status_code=404, detail="Metric not found")
    return await crud.upsert_event(session, metric_id, body)


@router.post("/{slug}/ingest", response_model=MetricEventOut, status_code=201)
async def ingest_metric(
    slug: str,
    body: MetricIngest,
    x_ingest_token: str | None = Header(default=None),
    session: AsyncSession = Depends(get_session),
):
    _verify_ingest_token(x_ingest_token)
    defaults = INGEST_METRIC_DEFAULTS.get(slug)
    if not defaults:
        raise HTTPException(status_code=404, detail=f"Unknown ingest source: {slug}")

    metric = await crud.get_or_create_metric_by_slug(session, slug, defaults)
    return await crud.upsert_event(
        session, metric.id, MetricEventCreate(date=body.date, value=body.value, meta=body.meta)
    )
