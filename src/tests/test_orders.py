import pytest
from httpx import AsyncClient
from src.models.movies import Movie
from src.models.orders import Order, OrderItem, OrderStatusEnum

@pytest.mark.asyncio
async def test_checkout_already_purchased_movie_raises_error(ac: AsyncClient, db_session):
    # 1. Создаем пользователя и делаем его активным
    # ... (код создания тестового юзера с авторизацией)
    headers = {"Authorization": "Bearer fake_test_jwt_token"}

    # 2. Создаем фильм в БД
    test_movie = Movie(
        uuid="test-uuid-111", name="Inception", year=2010, time=148, 
        imdb=8.8, description="Dream within a dream", price=9.99, certification_id=1
    )
    db_session.add(test_movie)
    await db_session.commit()

    # 3. Симулируем, что этот фильм уже БЫЛ куплен ранее (создаем PAID заказ)
    past_order = Order(user_id=1, status=OrderStatusEnum.PAID, total_amount=9.99)
    db_session.add(past_order)
    await db_session.flush()
    
    order_item = OrderItem(order_id=past_order.id, movie_id=test_movie.id, price_at_order=9.99)
    db_session.add(order_item)
    await db_session.commit()

    # 4. Пытаемся добавить этот же фильм в корзину
    # Наша бизнес-логика из Шага 3 должна заблокировать это на этапе добавления в корзину
    cart_payload = {"movie_id": test_movie.id}
    response = await ac.post("/cart/items", json=cart_payload, headers=headers)
    
    assert response.status_code == 400
    assert "already purchased" in response.json()["detail"]