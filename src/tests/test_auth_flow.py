import pytest
from httpx import AsyncClient
from sqlalchemy import select
from src.models.auth import ActivationToken, User

@pytest.mark.asyncio
async def test_full_auth_and_activation_flow(ac: AsyncClient, db_session):
    # 1. Регистрация нового пользователя
    reg_payload = {
        "email": "testuser@example.com",
        "password": "SecurePassword123"
    }
    reg_response = await ac.post("/auth/register", json=reg_payload)
    assert reg_response.status_code == 210  # Или 201 в зависимости от реализации статуса
    
    # 2. Проверяем, что пользователь создан, но не активен
    user_query = await db_session.execute(select(User).where(User.email == "testuser@example.com"))
    user = user_query.scalars().first()
    assert user is not None
    assert user.is_active is False

    # 3. Извлекаем созданный токен активации из базы данных
    token_query = await db_session.execute(select(ActivationToken).where(ActivationToken.user_id == user.id))
    act_token = token_query.scalars().first()
    assert act_token is not None

    # 4. Активируем аккаунт через GET-запрос по токену
    activation_response = await ac.get(f"/auth/activate/{act_token.token}")
    assert activation_response.status_code == 200
    
    # Проверяем, что статус сменился на active
    await db_session.refresh(user)
    assert user.is_active is True

    # 5. Выполняем Login
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