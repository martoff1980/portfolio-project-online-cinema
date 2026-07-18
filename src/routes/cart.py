from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from src.database import get_db
from src.models.cart import Cart, CartItem
from src.models.movies import Movie
from src.models.orders import Order, OrderItem
from src.schemas.cart import CartItemAdd, CartResponse
from src.dependencies import get_current_user

router = APIRouter(prefix="/cart", tags=["Shopping Cart"])


async def get_or_create_cart(user_id: int, db: AsyncSession) -> Cart:
    """Вспомогательная функция получения или создания корзины пользователя."""
    stmt = (
        select(Cart)
        .where(Cart.user_id == user_id)
        .options(selectinload(Cart.items).selectinload(CartItem.movie))
    )
    result = await db.execute(stmt)
    cart = result.scalars().first()

    if not cart:
        cart = Cart(user_id=user_id)
        db.add(cart)
        await db.commit()
        # Загружаем заново со связями
        result = await db.execute(stmt)
        cart = result.scalars().first()

    return cart


@router.get("/", response_model=CartResponse)
async def get_cart(
    db: AsyncSession = Depends(get_db),
    user=Depends(get_current_user)
):
    cart = await get_or_create_cart(user.id, db)

    # Считаем сумму цен всех фильмов в корзине
    total_price = sum(float(item.movie.price) for item in cart.items)

    return {
        "id": cart.id,
        "user_id": cart.user_id,
        "items": cart.items,
        "total_price": total_price,
    }


@router.post("/items", status_code=status.HTTP_201_CREATED)
async def add_item_to_cart(
    payload: CartItemAdd,
    db: AsyncSession = Depends(get_db),
    user=Depends(get_current_user),
):
    # 1. Проверяем, существует ли фильм вообще
    movie = await db.get(Movie, payload.movie_id)
    if not movie:
        raise HTTPException(status_code=404, detail="Movie not found.")

    # 2. Проверяем, не купил ли пользователь этот фильм ранее (Бизнес-правило!)
    # Ищем оплаченные (PAID) заказы пользователя, в которых есть этот фильм
    purchased_stmt = (
        select(OrderItem)
        .join(Order)
        .where(
            Order.user_id == user.id,
            Order.status == "PAID",  # ИЛИ OrderStatusEnum.PAID
            OrderItem.movie_id == payload.movie_id,
        )
    )
    already_purchased = (await db.execute(purchased_stmt)).scalars().first()
    if already_purchased:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="You have already purchased this movie. "
                   "No need to add it to the cart.",
        )

    # 3. Получаем корзину
    cart = await get_or_create_cart(user.id, db)

    # 4. Проверяем, нет ли уже этого фильма в корзине
    for item in cart.items:
        if item.movie_id == payload.movie_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="This movie is already in your cart.",
            )

    # 5. Добавляем в корзину
    new_item = CartItem(cart_id=cart.id, movie_id=payload.movie_id)
    db.add(new_item)
    await db.commit()

    return {
        "message": f"Movie '{movie.name}' successfully added to your cart."
    }


@router.delete("/items/{movie_id}", status_code=status.HTTP_204_NO_CONTENT)
async def remove_item_from_cart(
    movie_id: int,
    db: AsyncSession = Depends(get_db),
    user=Depends(get_current_user)
):
    cart = await get_or_create_cart(user.id, db)

    # Ищем элемент в корзине
    item_to_remove = None
    for item in cart.items:
        if item.movie_id == movie_id:
            item_to_remove = item
            break

    if not item_to_remove:
        raise HTTPException(
            status_code=404,
            detail="Movie not found in your cart."
        )

    await db.delete(item_to_remove)
    await db.commit()
    return None


@router.delete("/clear", status_code=status.HTTP_204_NO_CONTENT)
async def clear_cart(
    db: AsyncSession = Depends(get_db), user=Depends(get_current_user)
):
    cart = await get_or_create_cart(user.id, db)

    for item in cart.items:
        await db.delete(item)

    await db.commit()
    return None
