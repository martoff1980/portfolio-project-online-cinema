import enum
from datetime import datetime
from typing import List
from sqlalchemy import (
    Integer,
    ForeignKey,
    DateTime,
    String,
    Numeric,
    Enum as SQLEnum
)
from sqlalchemy.orm import Mapped, mapped_column, relationship
from src.models.movies import  Movie 
from src.models.auth import Base, User

class OrderStatusEnum(str, enum.Enum):
    PENDING = "pending"   # Заказ создан, ожидает оплаты
    PAID = "paid"         # Заказ успешно оплачен
    CANCELED = "canceled" # Заказ отменен

class Order(Base):
    __tablename__ = "orders"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    status: Mapped[OrderStatusEnum] = mapped_column(
        SQLEnum(OrderStatusEnum), default=OrderStatusEnum.PENDING, nullable=False
    )
    total_amount: Mapped[Numeric] = mapped_column(Numeric(10, 2), nullable=False)

    # Отношения
    user: Mapped["User"] = relationship()
    items: Mapped[List["OrderItem"]] = relationship("OrderItem", back_populates="order", cascade="all, delete-orphan")


class OrderItem(Base):
    __tablename__ = "order_items"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    order_id: Mapped[int] = mapped_column(ForeignKey("orders.id", ondelete="CASCADE"), nullable=False)
    movie_id: Mapped[int] = mapped_column(ForeignKey("movies.id", ondelete="CASCADE"), nullable=False)
    price_at_order: Mapped[Numeric] = mapped_column(Numeric(10, 2), nullable=False)  # Фиксация цены

    # Отношения
    order: Mapped["Order"] = relationship("Order", back_populates="items")
    movie: Mapped["Movie"] = relationship()