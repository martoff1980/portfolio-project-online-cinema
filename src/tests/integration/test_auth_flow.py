import pytest_asyncio
from httpx import AsyncClient
from sqlalchemy import select
from src.models.auth import ActivationToken, User


@pytest_asyncio.fixture(scope="function")
async def test_full_auth_and_activation_flow(
    ac: AsyncClient,
    db_session
):
    # New user registration
    reg_payload = {
        "email": "testuser@example.com",
        "password": "SecurePassword123"
    }
    reg_response = await ac.post("/auth/register", json=reg_payload)
    assert reg_response.status_code == 201

    # Check the user in the database and ensure they are inactive
    user_query = await db_session.execute(
        select(User).where(User.email == "testuser@example.com")
    )
    user = user_query.scalars().first()
    assert user is not None
    assert user.is_active is False

    # Retrieve the created activation token from the database.
    token_query = await db_session.execute(
        select(ActivationToken).where(ActivationToken.user_id == user.id)
    )
    act_token = token_query.scalars().first()
    assert act_token is not None

    # Activation endpoint should be a GET request
    # that activates the user account
    activation_response = await ac.get(f"/auth/activate/{act_token.token}")
    assert activation_response.status_code == 200

    # Check the user status after activation
    await db_session.refresh(user)
    assert user.is_active is True

    # Login
    login_payload = {
        "email": "testuser@example.com",
        "password": "SecurePassword123"
    }
    login_response = await ac.post("/auth/login", json=login_payload)
    assert login_response.status_code == 200

    token_data = login_response.json()
    assert "access_token" in token_data
    assert "refresh_token" in token_data
    assert token_data["token_type"] == "bearer"
