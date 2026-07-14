from typing import AsyncGenerator
from sqlalchemy.ext.asyncio import (
    create_async_engine,
    AsyncSession,
    async_sessionmaker
)
from sqlalchemy.orm import DeclarativeBase
from src.config import settings

# 1. Создаем асинхронный движок для работы с PostgreSQL через asyncpg
DATABASE_URL = settings.get_database_url()
engine = create_async_engine(
    DATABASE_URL,
    echo=False,  # Измени на True, если нужно видеть генерируемые SQL-запросы в консоли
    future=True
)

# 2. Создаем фабрику асинхронных сессий
AsyncSessionLocal = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autocommit=False,
    autoflush=False
)


# 3. Базовый декларативный класс для всех моделей SQLAlchemy
class Base(DeclarativeBase):
    pass


# 4. Dependency Injection для FastAPI, предоставляющий сессию БД на каждый запрос
async def get_db() -> AsyncGenerator[AsyncSession, None]:
    async with AsyncSessionLocal() as session:
        try:
            yield session
        finally:
            await session.close()