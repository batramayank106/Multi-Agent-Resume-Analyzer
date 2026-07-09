import logging
from collections.abc import AsyncGenerator

from sqlalchemy import create_engine, text
from sqlalchemy.orm import DeclarativeBase, sessionmaker
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker

from config import settings

logger = logging.getLogger(__name__)


class Base(DeclarativeBase):
    pass


sync_engine = create_engine(
    settings.database_url.replace("+aiosqlite", ""),
    echo=settings.debug,
    connect_args={"check_same_thread": False},
)

async_engine = create_async_engine(
    settings.database_url,
    echo=settings.debug,
)

SyncSessionLocal = sessionmaker(bind=sync_engine, autocommit=False, autoflush=False)
AsyncSessionLocal = async_sessionmaker(bind=async_engine, class_=AsyncSession, expire_on_commit=False)


def init_db():
    Base.metadata.create_all(bind=sync_engine)
    logger.info("Database tables created successfully")


async def get_async_session() -> AsyncGenerator[AsyncSession, None]:
    async with AsyncSessionLocal() as session:
        try:
            yield session
        finally:
            await session.close()


def get_sync_session():
    session = SyncSessionLocal()
    try:
        return session
    finally:
        session.close()
