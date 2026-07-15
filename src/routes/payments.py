import os
import stripe
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Header, Request, status
from sqlalchemy import select, Numeric
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from src.database import get_db
from src.models.orders import Order, OrderItem, OrderStatusEnum
from src.models.payments import Payment, PaymentItem, PaymentStatusEnum
from src.schemas.payments import PaymentResponse
from src.dependencies import get_current_user, allow_admin_only

router = APIRouter(prefix="/payments", tags=["Payments System"])

STRIPE_WEBHOOK_SECRET = os.getenv("STRIPE_WEBHOOK_SECRET", "")
stripe.api_key = os.getenv("STRIPE_API_KEY", "")


@router.post("/webhook", status_code=status.HTTP_200_OK)
async def stripe_webhook(
    request: Request,
    stripe_signature: str = Header(None),
    db: AsyncSession = Depends(get_db)
):
    """
    Асинхронный обработчик событий от Stripe.
    Проверяет валидность подписи Stripe Signature и обрабатывает успешную оплату.
    """
    payload = await request.body()
    
    try:
        # Проверка подписи Stripe, чтобы избежать поддельных запросов
        event = stripe.Webhook.construct_event(
            payload, stripe_signature, STRIPE_WEBHOOK_SECRET
        )
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid payload")
    except stripe.error.SignatureVerificationError:
        raise HTTPException(status_code=400, detail="Invalid signature")

    # Обработка успешного завершения сессии оплаты
    if event["type"] == "checkout.session.completed":
        session = event["data"]["object"]
        
        order_id = int(session["metadata"]["order_id"])
        external_payment_id = session["id"]
        amount_paid = Numeric(session["amount_total"]) / 100  # Переводим центы в доллары

        # 1. Ищем заказ в БД
        stmt = select(Order).where(Order.id == order_id).options(selectinload(Order.items))
        order = (await db.execute(stmt)).scalars().first()
        
        if order and order.status == OrderStatusEnum.PENDING:
            # 2. Обновляем статус заказа
            order.status = OrderStatusEnum.PAID
            
            # 3. Фиксируем успешную транзакцию
            payment = Payment(
                user_id=order.user_id,
                order_id=order.id,
                status=PaymentStatusEnum.SUCCESSFUL,
                amount=amount_paid,
                external_payment_id=external_payment_id
            )
            db.add(payment)
            await db.flush()

            # 4. Создаем детализацию платежа для каждой позиции
            for order_item in order.items:
                payment_item = PaymentItem(
                    payment_id=payment.id,
                    order_item_id=order_item.id,
                    price_at_payment=order_item.price_at_order
                )
                db.add(payment_item)
            
            await db.commit()
            
            # (Опционально): Отправка email пользователю о покупке
            # send_receipt_email.delay(order.user_id, order.id)

    return {"status": "success"}


# --- Пользовательский эндпоинт просмотра истории платежей ---
@router.get("/my-history", response_model=List[PaymentResponse])
async def get_my_payments(
    db: AsyncSession = Depends(get_db),
    user = Depends(get_current_user)
):
    stmt = (
        select(Payment)
        .where(Payment.user_id == user.id)
        .options(selectinload(Payment.items))
    )
    payments = (await db.execute(stmt)).scalars().all()
    return payments


# --- Панель администратора: мониторинг всех транзакций ---
@router.get("/all-payments", response_model=List[PaymentResponse])
async def get_all_payments(
    user_id: Optional[int] = None,
    status: Optional[PaymentStatusEnum] = None,
    db: AsyncSession = Depends(get_db),
    admin = Depends(allow_admin_only)  # Доступ только Администраторам
):
    query = select(Payment).options(selectinload(Payment.items))
    if user_id:
        query = query.where(Payment.user_id == user_id)
    if status:
        query = query.where(Payment.status == status)
        
    result = await db.execute(query)
    return result.scalars().all()