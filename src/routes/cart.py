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
    """Helper function to retrieve or create a user's shopping cart."""
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
        # Load the cart again to include the items relationship
        result = await db.execute(stmt)
        cart = result.scalars().first()

        if cart is None:
            raise RuntimeError("Failed to create cart")

    return cart


@router.get("/", response_model=CartResponse)
async def get_cart(
    db: AsyncSession = Depends(get_db),
    user=Depends(get_current_user)
):
    cart = await get_or_create_cart(user.id, db)

    # Count summation of the prices of all movies in the cart
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
    # Check if the movie exists in the database
    movie = await db.get(Movie, payload.movie_id)
    if not movie:
        raise HTTPException(status_code=404, detail="Movie not found.")

    # Chech if the user has already purchased this movie
    # Search for paid orders of the user that contain this movie
    purchased_stmt = (
        select(OrderItem)
        .join(Order)
        .where(
            Order.user_id == user.id,
            # Alternative OrderStatusEnum.PAID
            Order.status == "PAID",
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

    # Get cart
    cart = await get_or_create_cart(user.id, db)

    # Check if the movie is already in the cart
    for item in cart.items:
        if item.movie_id == payload.movie_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="This movie is already in your cart.",
            )

    # add the movie to the cart
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

    # Search for the item in the cart
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
