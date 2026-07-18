from pydantic import BaseModel, Field
from typing import List
from src.schemas.movies import MovieResponse


class CartItemAdd(BaseModel):
    movie_id: int = Field(..., gt=0)


class CartItemResponse(BaseModel):
    id: int
    movie: MovieResponse

    class Config:
        from_attributes = True


class CartResponse(BaseModel):
    id: int
    user_id: int
    items: List[CartItemResponse]
    total_price: float = Field(
        0.0,
        description="Total cost of all movies in the cart"
    )

    class Config:
        from_attributes = True
