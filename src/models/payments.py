import enum
from datetime import datetime
from typing import List, Optional
from decimal import Decimal
from sqlalchemy import Integer, ForeignKey, DateTime, String, Decimal as SQlDecimal, Enum as SQLEnum
from sqlalchemy.orm import Mapped, mapped_column, relationship
from src.models.auth import Base, User
from src.models.orders import Order, OrderItem

class PaymentStatusEnum(str, enum.Enum):
    SUCCESSFUL = "successful"  # Платеж успешно завершен
    CANCELED = "canceled"      # Платеж был отменен
    REFUNDED = "refunded"      # Оформлен возврат средств

class Payment(Base):
    __tablename__ = "payments"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    order_id: Mapped[int] = mapped_column(ForeignKey("orders.id", ondelete="CASCADE"), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    status: Mapped[PaymentStatusEnum] = mapped_column(
        SQLEnum(PaymentStatusEnum), default=PaymentStatusEnum.SUCCESSFUL, nullable=False
    )
    amount: Mapped[Decimal] = mapped_column(SQlDecimal(10, 2), nullable=False)  # Итоговая сумма транзакции
    external_payment_id: Mapped[Optional[str]] = mapped_column(String, nullable=True)  # ID сессии или транзакции в Stripe

    # Отношения
    user: Mapped["User"] = relationship()
    order: Mapped["Order"] = relationship()
    items: Mapped[List["PaymentItem"]] = relationship("PaymentItem", back_populates="payment", cascade="all, delete-orphan")


class PaymentItem(Base):
    __tablename__ = "payment_items"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    payment_id: Mapped[int] = mapped_column(ForeignKey("payments.id", ondelete="CASCADE"), nullable=False)
    order_item_id: Mapped[int] = mapped_column(ForeignKey("order_items.id", ondelete="CASCADE"), nullable=False)
    price_at_payment: Mapped[Decimal] = mapped_column(SQlDecimal(10, 2), nullable=False)  # Фиксация цены в чеке

    # Отношения
    payment: Mapped["Payment"] = relationship("Payment", back_populates="items")
    order_item: Mapped["OrderItem"] = relationship()