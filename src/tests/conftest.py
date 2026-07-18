import asyncio
import pytest
import pytest_asyncio
from typing import AsyncGenerator
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from httpx import AsyncClient

from src.main import app
from src.database import get_db
from src.models.auth import Base, UserGroup, UserGroupEnum

# Тестовая база данных (внутри контейнера или локальная)
TEST_DATABASE_URL = "postgresql+asyncpg://cinema_test_user:cinema_test_pass@localhost:5432/online_cinema_test_db"

engine_test = create_async_engine(TEST_DATABASE_URL, echo=False)
async_session_maker = async_sessionmaker(engine_test, expire_on_commit=False, class_=AsyncSession)

@pytest.fixture(scope="session")
# @pytest_asyncio.fixture(scope="function")
def event_loop():
    """Создает экземпляр event loop для всей тестовой сессии."""
    policy = asyncio.get_event_loop_policy()
    loop = policy.new_event_loop()
    yield loop
    loop.close()

@pytest.fixture(scope="session", autouse=True)
# @pytest_asyncio.fixture(scope="function", autouse=True)
async def prepare_database():
    """Автоматически создает таблицы перед тестами и удаляет после."""
    async with engine_test.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    
    # Наполняем дефолтными ролями
    async with async_session_maker() as session:
        for role in UserGroupEnum:
            group = UserGroup(name=role)
            session.add(group)
        await session.commit()

    yield
    
    async with engine_test.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)

@pytest.fixture
# @pytest_asyncio.fixture(scope="function")
async def db_session() -> AsyncGenerator[AsyncSession, None]:
    """Фикстура для получения изолированной сессии БД в каждом тесте."""
    async with async_session_maker() as session:
        yield session

@pytest.fixture
# @pytest_asyncio.fixture(scope="function")
async def ac(db_session: AsyncSession) -> AsyncGenerator[AsyncClient, None]:
    """Асинхронный HTTP-клиент, подменяющий реальную сессию БД на тестовую."""
    def _get_test_db():
        return db_session

    app.dependency_overrides[get_db] = _get_test_db
    async with AsyncClient(app=app, base_url="http://test") as client:
        yield client
    app.dependency_overrides.clear()