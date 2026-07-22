from pydantic import BaseModel, Field, ConfigDict
from typing import List
from src.schemas.movies import MovieResponse


class CartItemAdd(BaseModel):
    movie_id: int = Field(..., gt=0)


class CartItemResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    movie: MovieResponse


class CartResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    user_id: int
    items: List[CartItemResponse]
    total_price: float = Field(
        0.0,
        description="Total cost of all movies in the cart"
    )
