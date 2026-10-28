import os

# Must be set before importing the app, because config.py reads it at import time
os.environ.setdefault("RIOT_API_KEY", "RGAPI-test")

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine
from sqlalchemy.pool import NullPool, StaticPool

from app import models  # noqa: F401  (registers tables on Base)
from app.db import Base, get_session
from app.main import app, get_riot
from app.schemas import MatchSummary

TEST_DB_URL = os.getenv("TEST_DATABASE_URL", "sqlite+aiosqlite://")

def make_test_engine():
    if TEST_DB_URL.startswith("sqlite"):
        return create_async_engine(
            TEST_DB_URL,
            poolclass=StaticPool,
            connect_args={"check_same_thread": False},
        )
    # NullPool avoids "attached to a different event loop" errors with asyncpg
    return create_async_engine(TEST_DB_URL, poolclass=NullPool)

class FakeRiot:
    """Stands in for RiotClient and records every get_match_summary call."""

    def __init__(self):
        self.match_ids: list[str] = []
        self.summary_calls: list[str] = []

    async def get_puuid(self, game_name: str, tag_line: str) -> str:
        return "puuid-123"

    async def get_match_ids(self, puuid: str, count: int = 20) -> list[str]:
        return self.match_ids

    async def get_match_summary(self, match_id: str, puuid: str) -> MatchSummary:
        self.summary_calls.append(match_id)
        n = int(match_id[1:])  # "M4" -> 4, gives each match a distinct game_start
        return MatchSummary(
            match_id=match_id,
            champion="Ahri",
            win=True,
            kills=n,
            deaths=1,
            assists=2,
            cs=100,
            duration_seconds=1800,
            game_start=1_700_000_000_000 + n,
        )


@pytest.fixture
def fake_riot() -> FakeRiot:
    return FakeRiot()


@pytest_asyncio.fixture
async def session_factory():
    # StaticPool keeps one shared connection. Without it, every new connection
    # to "sqlite://" would get its own empty in-memory database.
    engine = create_async_engine(
        "sqlite+aiosqlite://",
        poolclass=StaticPool,
        connect_args={"check_same_thread": False},
    )
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield async_sessionmaker(engine, expire_on_commit=False)
    await engine.dispose()


@pytest_asyncio.fixture
async def client(session_factory, fake_riot):
    async def override_session():
        async with session_factory() as session:
            yield session

    app.dependency_overrides[get_session] = override_session
    app.dependency_overrides[get_riot] = lambda: fake_riot

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as c:
        yield c

    app.dependency_overrides.clear()