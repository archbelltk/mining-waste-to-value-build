"""Test fixtures: a throwaway test database + an httpx client wired to it.

Like what you know: this plays the role a Jest/Vitest global setup file plus
a Supertest `request(app)` helper would play together — one fixture spins up
isolated test state, the other gives you an HTTP client against the app.
"""

from collections.abc import AsyncGenerator

import asyncpg
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.core.config import get_settings
from app.core.database import get_db
from app.main import app
from app.models import Base

settings = get_settings()
TEST_DB_NAME = "mwtv_test"


def _admin_url() -> str:
    # Same server as DATABASE_URL, but connecting to the maintenance DB so we
    # can create/drop the throwaway test database.
    base = settings.database_url.replace("postgresql+asyncpg://", "postgresql://")
    return base.rsplit("/", 1)[0] + "/postgres"


def _test_db_url() -> str:
    base = settings.database_url.rsplit("/", 1)[0]
    return f"{base}/{TEST_DB_NAME}"


@pytest_asyncio.fixture(scope="session", autouse=True)
async def _test_database() -> AsyncGenerator[None, None]:
    conn = await asyncpg.connect(_admin_url())
    try:
        await conn.execute(f'DROP DATABASE IF EXISTS "{TEST_DB_NAME}" WITH (FORCE)')
        await conn.execute(f'CREATE DATABASE "{TEST_DB_NAME}"')
    finally:
        await conn.close()

    from sqlalchemy import text

    engine = create_async_engine(_test_db_url())
    async with engine.begin() as connection:
        await connection.execute(text("CREATE EXTENSION IF NOT EXISTS postgis"))
        await connection.execute(text("CREATE EXTENSION IF NOT EXISTS vector"))
        await connection.execute(text("CREATE EXTENSION IF NOT EXISTS pgcrypto"))
        await connection.run_sync(Base.metadata.create_all)
    await engine.dispose()

    yield

    conn = await asyncpg.connect(_admin_url())
    try:
        await conn.execute(f'DROP DATABASE IF EXISTS "{TEST_DB_NAME}" WITH (FORCE)')
    finally:
        await conn.close()


@pytest_asyncio.fixture
async def db_session() -> AsyncGenerator[AsyncSession, None]:
    engine = create_async_engine(_test_db_url())
    session_maker = async_sessionmaker(engine, expire_on_commit=False)
    async with session_maker() as session:
        yield session
    await engine.dispose()


@pytest_asyncio.fixture
async def client(db_session: AsyncSession) -> AsyncGenerator[AsyncClient, None]:
    async def _override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = _override_get_db
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac
    app.dependency_overrides.clear()
