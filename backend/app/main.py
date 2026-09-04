"""Habit Heatmap Dashboard — FastAPI app."""
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

load_dotenv()

logging.basicConfig(
    level=os.getenv("LOG_LEVEL", "INFO"),
    format="%(asctime)s %(levelname)s %(name)s: %(message)s",
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    await init_db()
    async with async_session() as session:
        github_token = os.getenv("GITHUB_TOKEN")
        github_login = os.getenv("GITHUB_LOGIN")
        if github_token and github_login:
            try:
                await sync_github_metric(session, github_login, github_token)
            except Exception:
                logger.exception("GitHub sync failed at startup, falling back to mock data")
                await session.rollback()
                await seed_if_empty(session)
        else:
            await seed_if_empty(session)
    logger.info("Habit Heatmap Dashboard API started")
    yield


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
