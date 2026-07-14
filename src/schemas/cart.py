from pydantic import BaseModel, Field
from typing import List, Optional
from schemas import MovieResponse  # Импортируем схему фильма из Шага 2

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
    total_price: float = Field(0.0, description="Суммарная стоимость всех фильмов в корзине")

    class Config:
        from_attributes = True