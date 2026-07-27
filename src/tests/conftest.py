import pytest_asyncio
from typing import AsyncGenerator
from sqlalchemy.ext.asyncio import (
    create_async_engine,
    AsyncSession,
    async_sessionmaker
)
from httpx import AsyncClient

from src.main import app
from src.database import get_db
from src.models.auth import Base, UserGroup, UserGroupEnum

# Test db (inside container)
TEST_DATABASE_URL = (
    "postgresql+asyncpg://"
    "cinema_test_user:cinema_test_pass"
    "@localhost:5432/online_cinema_test_db"
)

engine_test = create_async_engine(TEST_DATABASE_URL, echo=False)
async_session_maker = async_sessionmaker(
    engine_test,
    expire_on_commit=False,
    class_=AsyncSession
)


@pytest_asyncio.fixture(scope="function", autouse=True)
async def prepare_database():
    """
    Automatically creates tables before tests and deletes them afterwards.
    """
    async with engine_test.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)

    # Default roles: ADMIN, USER, GUEST
    async with async_session_maker() as session:
        for role in UserGroupEnum:
            group = UserGroup(name=role)
            session.add(group)
        await session.commit()

    yield

    async with engine_test.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)

    # Close all connections in the connection pool
    await engine_test.dispose()


@pytest_asyncio.fixture(scope="function")
async def db_session() -> AsyncGenerator[AsyncSession, None]:
    """
    A fixture for obtaining an isolated database session in each test.
    """
    connection = await engine_test.connect()
    transaction = await connection.begin()

    session = AsyncSession(bind=connection, expire_on_commit=False)

    yield session

    await session.close()
    await transaction.rollback()
    await connection.close()


@pytest_asyncio.fixture(scope="function")
async def ac(db_session: AsyncSession) -> AsyncGenerator[AsyncClient, None]:
    """
    An asynchronous HTTP client that swaps the real database session
    for a test session.
    """
    # We redefine get_db so that it returns the same db_session
    # as the one used in the test.
    async def _override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = _override_get_db

    async with AsyncClient(app=app, base_url="http://test") as client:
        yield client
    app.dependency_overrides.clear()
