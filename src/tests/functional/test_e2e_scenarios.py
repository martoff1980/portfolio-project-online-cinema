import uuid
import pytest
from sqlalchemy import select

from src.models.auth import User
from src.models.movies import Movie, Genre, Certification


@pytest.mark.asyncio
async def test_complete_user_buy_movie_flow(ac, db_session):
    # New user registration
    user_email = "buyer@test.com"
    reg_response = await ac.post(
        "/auth/register",
        json={"email": user_email, "password": "UserPass123!"}
    )

    assert reg_response.status_code in (200, 201), (
        f"Registration failed: {reg_response.text}"
    )

    result = await db_session.execute(
        select(User).where(User.email == user_email)
    )
    user = result.scalar_one()

    # Меняем флаг активности и фиксируем изменения в БД
    user.is_active = True
    await db_session.commit()
    await db_session.refresh(user)

    # Authorization
    login_res = await ac.post(
        "/auth/login",
        json={"email": user_email, "password": "UserPass123!"}
    )
    # ПРОВЕРКА 1: Убедимся, что сервер вернул 200 OK, а не 400/422
    assert login_res.status_code == 200, (
        f"Login failed with status {login_res.status_code}:"
        f"{login_res.text}"
    )
    token = login_res.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    # 3. ПОДГОТОВКА ДАННЫХ: Создаем жанр Drama и фильм в тестовой БД
    certification = Certification(name="PG-13")
    db_session.add(certification)

    genre_drama = Genre(name="Drama")
    db_session.add(genre_drama)
    await db_session.commit()

    test_movie = Movie(
        uuid=str(uuid.uuid4()),
        name="Test Movie",
        description="E2E test movie description",
        price=10.00,
        year=2023,
        time=120,
        imdb=8.5,
        certification_id=certification.id,
        genres=[genre_drama]
    )
    db_session.add(test_movie)
    await db_session.commit()

    # Browsing and filtering the catalog
    catalog_res = await ac.get(
        "/movies?genre=Drama", headers=headers, follow_redirects=True
    )
    assert catalog_res.status_code == 200
    movie_id = catalog_res.json()[0]["id"]

    # Adding the movie to the cart
    cart_res = await ac.post(
        "/cart/items",
        json={"movie_id": movie_id},
        headers=headers
    )
    assert cart_res.status_code == 201

    # Placing an order
    order_res = await ac.post("/orders/checkout", headers=headers)
    assert order_res.status_code == 200

    order_payload = order_res.json()
    # Printing sructure JSON if order_id not exist in result
    assert "order_id" in order_payload or "data" in order_payload, (
        f"Unexpected order response format: {order_payload}"
    )

    order_id = order_res.json()["order_id"]  
    assert order_id is not None

    # Checking order status after placement
    order_check = await ac.get(
        f"/orders/{order_id}/mock-payment?status=success",
        headers=headers
    )
    assert order_check.status_code == 200
    assert order_check.json()["message"] == (
        "Mock payment successful. Order has been paid."
    )
