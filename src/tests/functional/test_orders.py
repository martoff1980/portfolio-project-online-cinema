import pytest_asyncio
from httpx import AsyncClient
from src.models.movies import Movie
from src.models.orders import Order, OrderItem, OrderStatusEnum


@pytest_asyncio.fixture(scope="function")
async def test_checkout_already_purchased_movie_raises_error(
    ac: AsyncClient,
    db_session
):
    # Create a test user and simulate that they are logged in
    # (for simplicity, we will just use a fake JWT token)
    headers = {"Authorization": "Bearer fake_test_jwt_token"}

    # Create movie in the database
    test_movie = Movie(
        uuid="test-uuid-111",
        name="Inception",
        year=2010,
        time=148,
        imdb=8.8,
        description="Dream within a dream",
        price=9.99,
        certification_id=1
    )
    db_session.add(test_movie)
    await db_session.commit()

    # Create PAID order for the test user with the test movie
    past_order = Order(
        user_id=1,
        status=OrderStatusEnum.PAID,
        total_amount=9.99
    )
    db_session.add(past_order)
    await db_session.flush()

    order_item = OrderItem(
        order_id=past_order.id,
        movie_id=test_movie.id,
        price_at_order=9.99
    )
    db_session.add(order_item)
    await db_session.commit()

    # Try to add the same movie to the cart again
    # Bisiness logic should block this at the cart addition stage
    cart_payload = {"movie_id": test_movie.id}
    response = await ac.post("/cart/items", json=cart_payload, headers=headers)

    assert response.status_code == 400
    assert "already purchased" in response.json()["detail"]
