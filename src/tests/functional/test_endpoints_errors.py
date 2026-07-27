import pytest


@pytest.mark.asyncio
async def test_invalid_input_validation(ac):
    # Invalid email and password that is too short
    response = await ac.post("/auth/register", json={
        "email": "not-an-email",
        "password": "123"
    })
    assert response.status_code == 422
    assert "detail" in response.json()


@pytest.mark.asyncio
async def test_movie_filtering_and_sorting(ac, db_session):
    # Simulation of filtering and sorting
    response = await ac.get(
        "/movies",
        params={"genre": "Sci-Fi", "sort_by": "rating"}
    )
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
