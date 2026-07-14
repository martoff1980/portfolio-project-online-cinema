from pydantic import BaseModel, Field
from datetime import datetime
from typing import List
from src.models.orders import OrderStatusEnum
from src.schemas.movies import MovieResponse

class OrderItemResponse(BaseModel):
    id: int
    movie_id: int
    price_at_order: float
    movie: MovieResponse

    class Config:
        from_attributes = True

class OrderResponse(BaseModel):
    id: int
    user_id: int
    created_at: datetime
    status: OrderStatusEnum
    total_amount: float
    items: List[OrderItemResponse]

    class Config:
        from_attributes = True

class CheckoutResponse(BaseModel):
    order_id: int
    total_amount: float
    payment_url: str