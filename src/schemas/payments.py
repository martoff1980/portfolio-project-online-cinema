from pydantic import BaseModel, ConfigDict, ConfigDict
from datetime import datetime
from typing import List, Optional
from src.models.payments import PaymentStatusEnum


class PaymentItemResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    
    id: int
    order_item_id: int
    price_at_payment: float

    # class Config:
    #     from_attributes = True


class PaymentResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    user_id: int
    order_id: int
    created_at: datetime
    status: PaymentStatusEnum
    amount: float
    external_payment_id: Optional[str]
    items: List[PaymentItemResponse]

    # class Config:
    #     from_attributes = True
