from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import RedirectResponse
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from src.database import get_db
from src.models.cart import Cart, CartItem
from src.models.orders import Order, OrderItem, OrderStatusEnum
from src.models.movies import Movie
from src.schemas.orders import OrderResponse, CheckoutResponse
from src.dependencies import get_current_user, allow_admin_only
from src.stripe_service import create_payment_session

router = APIRouter(prefix="/orders", tags=["Orders & Payments"])


@router.post("/checkout", response_model=CheckoutResponse)
async def checkout(
    db: AsyncSession = Depends(get_db),
    user = Depends(get_current_user)
):
    # 1. Получаем корзину пользователя
    cart_stmt = select(Cart).where(Cart.user_id == user.id).options(
        selectinload(Cart.items).selectinload(CartItem.movie)
    )
    cart = (await db.execute(cart_stmt)).scalars().first()
    
    if not cart or not cart.items:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Your cart is empty. Cannot place an order."
        )

    # 2. Валидация: Проверяем, не куплены ли эти фильмы ранее
    movie_ids_in_cart = [item.movie_id for item in cart.items]
    
    purchased_stmt = (
        select(OrderItem.movie_id)
        .join(Order)
        .where(
            Order.user_id == user.id,
            Order.status == OrderStatusEnum.PAID,
            OrderItem.movie_id.in_(movie_ids_in_cart)
        )
    )
    purchased_ids = (await db.execute(purchased_stmt)).scalars().all()
    if purchased_ids:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Some movies in your cart have already been purchased (IDs: {list(purchased_ids)}). Please remove them."
        )

    # 3. Валидация: Проверяем, нет ли уже других PENDING заказов с этими же фильмами
    pending_stmt = (
        select(OrderItem.movie_id)
        .join(Order)
        .where(
            Order.user_id == user.id,
            Order.status == OrderStatusEnum.PENDING,
            OrderItem.movie_id.in_(movie_ids_in_cart)
        )
    )
    pending_ids = (await db.execute(pending_stmt)).scalars().all()
    if pending_ids:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="You already have a pending order containing some of these movies. Please pay or cancel that order first."
        )

    # 4. Рассчитываем итоговую сумму заказа
    total_amount = sum(item.movie.price for item in cart.items)

    # 5. Создаем заказ со статусом pending
    new_order = Order(
        user_id=user.id,
        status=OrderStatusEnum.PENDING,
        total_amount=total_amount
    )
    db.add(new_order)
    await db.flush()  # Получаем ID заказа

    # 6. Переносим элементы из корзины в детали заказа
    for cart_item in cart.items:
        order_item = OrderItem(
            order_id=new_order.id,
            movie_id=cart_item.movie_id,
            price_at_order=cart_item.movie.price  # Фиксируем цену на момент заказа
        )
        db.add(order_item)
        # Удаляем из корзины
        await db.delete(cart_item)

    await db.commit()

    # 7. Генерируем сессию оплаты Stripe или Заглушку
    payment_url = create_payment_session(new_order.id, float(total_amount), user.email)

    return {
        "order_id": new_order.id,
        "total_amount": float(total_amount),
        "payment_url": payment_url
    }


# --- Роут заглушки для локальной симуляции успешной оплаты ---
@router.get("/{order_id}/mock-payment")
async def mock_payment(
    order_id: int,
    status: str = "success",
    db: AsyncSession = Depends(get_db)
):
    order = await db.get(Order, order_id)
    if not order:
        raise HTTPException(status_code=404, detail="Order not found.")

    if status == "success":
        order.status = OrderStatusEnum.PAID
        await db.commit()
        # Тут также можно запустить Celery-задачу для отправки email-подтверждения пользователю
        return {"message": "Mock payment successful. Order has been paid."}
    else:
        order.status = OrderStatusEnum.CANCELED
        await db.commit()
        return {"message": "Mock payment failed. Order has been canceled."}


@router.get("/my-orders", response_model=List[OrderResponse])
async def get_my_orders(
    db: AsyncSession = Depends(get_db),
    user = Depends(get_current_user)
):
    stmt = (
        select(Order)
        .where(Order.user_id == user.id)
        .options(selectinload(Order.items).selectinload(OrderItem.movie))
    )
    orders = (await db.execute(stmt)).scalars().all()
    return orders


# --- Роут админов: просмотр заказов с фильтрами ---
@router.get("/all-orders", response_model=List[OrderResponse])
async def get_all_orders(
    user_id: int = None,
    status: OrderStatusEnum = None,
    db: AsyncSession = Depends(get_db),
    admin = Depends(allow_admin_only)  # Только администратор
):
    query = select(Order).options(selectinload(Order.items).selectinload(OrderItem.movie))
    if user_id:
        query = query.where(Order.user_id == user_id)
    if status:
        query = query.where(Order.status == status)
        
    result = await db.execute(query)
    return result.scalars().all()