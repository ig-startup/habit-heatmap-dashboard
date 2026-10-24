"""Router: /api/competition — Брат (GitHub) vs Ты (статьи) points competition."""
from datetime import date, timedelta

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app import crud
from app.db import get_session
from app.schemas import CompetitionDailyPoint, CompetitionOut, CompetitionPlayer, CompetitionWeekPoint
from app.scoring import GITHUB_PARAMS, OBSIDIAN_PARAMS, bucket_by_week, daily_points

router = APIRouter(prefix="/api/competition", tags=["competition"])

CHALLENGE_START = date(2026, 10, 12)  # понедельник; всё, что раньше, в соревновании не учитывается
WEEKS_WINDOW = 12

# Брат на старте — тот же GitHub-аккаунт как заглушка; реальный второй
# аккаунт позже меняет lookup, остальной код не трогается.
PLAYERS = [
    {
        "id": "brat",
        "label": "Брат",
        "icon": "🐙",
        "color": "#3fb950",
        "lookup": {"source_type": "github"},
        "params": GITHUB_PARAMS,
    },
    {
        "id": "ty",
        "label": "Ты",
        "icon": "📝",
        "color": "#a970ff",
        "lookup": {"slug": "obsidian"},
        "params": OBSIDIAN_PARAMS,
    },
]


@router.get("", response_model=CompetitionOut)
async def get_competition(session: AsyncSession = Depends(get_session)):
    window_weeks = [CHALLENGE_START + timedelta(weeks=i) for i in range(WEEKS_WINDOW)]

    players_out = []
    for cfg in PLAYERS:
        lookup = cfg["lookup"]
        metric = (
            await crud.get_metric_by_source_type(session, lookup["source_type"])
            if "source_type" in lookup
            else await crud.find_metric_by_slug(session, lookup["slug"])
        )
        events = await crud.all_events(session, metric.id) if metric else []

        scored = [
            (e.date, float(e.value), daily_points(float(e.value), cfg["params"]))
            for e in events
            if e.date >= CHALLENGE_START
        ]
        raw_by_week = bucket_by_week((d, v) for d, v, _ in scored)
        points_by_week = bucket_by_week((d, p) for d, _, p in scored)

        weekly = [
            CompetitionWeekPoint(
                week_start=wk,
                raw_total=raw_by_week.get(wk, 0.0),
                points_total=points_by_week.get(wk, 0.0),
            )
            for wk in window_weeks
        ]
        daily = [CompetitionDailyPoint(date=d, value=v, points=p) for d, v, p in scored]

        players_out.append(
            CompetitionPlayer(
                id=cfg["id"],
                label=cfg["label"],
                icon=cfg["icon"],
                color=cfg["color"],
                metric_found=metric is not None,
                daily=daily,
                weekly=weekly,
                cumulative_points=sum(p for _, _, p in scored),
            )
        )

    return CompetitionOut(start_date=CHALLENGE_START, weeks=WEEKS_WINDOW, players=players_out)
