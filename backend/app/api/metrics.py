"""Router: /api/metrics"""
from datetime import date

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app import crud
from app.db import get_session
from app.schemas import MetricCreate, MetricEventCreate, MetricEventOut, MetricWithStats

router = APIRouter(prefix="/api/metrics", tags=["metrics"])


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
