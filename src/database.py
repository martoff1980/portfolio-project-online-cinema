from typing import AsyncGenerator
from sqlalchemy.ext.asyncio import (
    create_async_engine,
    AsyncSession,
    async_sessionmaker
)
from sqlalchemy.orm import DeclarativeBase
from src.config import settings

# Creating an asynchronous engine for working with PostgreSQL via asyncpg
DATABASE_URL = settings.get_database_url()
engine = create_async_engine(
    DATABASE_URL,
    echo=False,
    future=True
)

# Create factory for asynchronous sessions
AsyncSessionLocal = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autocommit=False,
    autoflush=False
)


# Base class for SQLAlchemy models
class Base(DeclarativeBase):
    pass


# Dependency Injection for FastAPI, wich get database session for each request
async def get_db() -> AsyncGenerator[AsyncSession, None]:
    async with AsyncSessionLocal() as session:
        try:
            yield session
        finally:
            await session.close()
