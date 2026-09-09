"""Async SQLAlchemy engine/session setup.

Like what you know: `async_sessionmaker` here is Prisma's `PrismaClient` /
TypeORM's `DataSource` — one engine for the process, a fresh session per
request via the `get_db` FastAPI dependency below.
"""

from collections.abc import AsyncGenerator

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.core.config import get_settings

settings = get_settings()

engine = create_async_engine(settings.database_url, echo=settings.env == "development")

AsyncSessionLocal = async_sessionmaker(engine, expire_on_commit=False)


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    async with AsyncSessionLocal() as session:
        yield session
