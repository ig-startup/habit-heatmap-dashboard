import os

os.environ["DATABASE_URL"] = "sqlite+aiosqlite:///:memory:"
# Prevent load_dotenv() (in app.main) from picking up a real token from the repo-root
# .env and triggering a live GitHub sync during tests.
os.environ["GITHUB_TOKEN"] = ""
os.environ["GITHUB_LOGIN"] = ""

import pytest_asyncio
from httpx import ASGITransport, AsyncClient

from app.db import Base, engine
from app.main import app


@pytest_asyncio.fixture
async def client():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
