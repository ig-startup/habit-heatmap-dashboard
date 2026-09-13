"""Habit Heatmap Dashboard — FastAPI app."""
import asyncio
import contextlib
import logging
import os
from contextlib import asynccontextmanager

from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.metrics import router as metrics_router
from app.db import async_session, init_db
from app.seed_mock import seed_if_empty
from app.sync_github import sync_github_metric
from app.sync_metrika import sync_metrika_metric

load_dotenv()

logging.basicConfig(
    level=os.getenv("LOG_LEVEL", "INFO"),
    format="%(asctime)s %(levelname)s %(name)s: %(message)s",
)
logger = logging.getLogger(__name__)

GITHUB_SYNC_INTERVAL_SECONDS = int(os.getenv("GITHUB_SYNC_INTERVAL_SECONDS", 3 * 3600))
METRIKA_SYNC_INTERVAL_SECONDS = int(os.getenv("METRIKA_SYNC_INTERVAL_SECONDS", 3600))


async def _github_sync_loop(login: str, token: str) -> None:
    """Re-sync GitHub contributions on a fixed interval for the lifetime of the process.

    The container only restarts on deploy/crash (restart: unless-stopped), so without
    this loop the startup-only sync in `lifespan` goes stale after the first deploy.
    """
    while True:
        await asyncio.sleep(GITHUB_SYNC_INTERVAL_SECONDS)
        try:
            async with async_session() as session:
                await sync_github_metric(session, login, token)
        except Exception:
            logger.exception("Periodic GitHub sync failed")


async def _metrika_sync_loop(counter_id: str, token: str) -> None:
    """Re-sync Yandex Metrika visits on a fixed interval for the lifetime of the process."""
    while True:
        await asyncio.sleep(METRIKA_SYNC_INTERVAL_SECONDS)
        try:
            async with async_session() as session:
                await sync_metrika_metric(session, counter_id, token)
        except Exception:
            logger.exception("Periodic Yandex Metrika sync failed")


@asynccontextmanager
async def lifespan(app: FastAPI):
    await init_db()
    github_token = os.getenv("GITHUB_TOKEN")
    github_login = os.getenv("GITHUB_LOGIN")
    async with async_session() as session:
        if github_token and github_login:
            try:
                await sync_github_metric(session, github_login, github_token)
            except Exception:
                logger.exception("GitHub sync failed at startup, falling back to mock data")
                await session.rollback()
                await seed_if_empty(session)
        else:
            await seed_if_empty(session)

    metrika_token = os.getenv("YANDEX_METRIKA_TOKEN")
    metrika_counter_id = os.getenv("YANDEX_METRIKA_COUNTER_ID")
    if metrika_token and metrika_counter_id:
        async with async_session() as session:
            try:
                await sync_metrika_metric(session, metrika_counter_id, metrika_token)
            except Exception:
                logger.exception("Yandex Metrika sync failed at startup")
                await session.rollback()

    sync_tasks = []
    if github_token and github_login:
        sync_tasks.append(asyncio.create_task(_github_sync_loop(github_login, github_token)))
    if metrika_token and metrika_counter_id:
        sync_tasks.append(asyncio.create_task(_metrika_sync_loop(metrika_counter_id, metrika_token)))

    logger.info("Habit Heatmap Dashboard API started")
    yield

    for task in sync_tasks:
        task.cancel()
        with contextlib.suppress(asyncio.CancelledError):
            await task


app = FastAPI(title="Habit Heatmap Dashboard API", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=os.getenv("CORS_ORIGINS", "*").split(","),
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(metrics_router)


@app.get("/health")
def health():
    return {"status": "ok"}
