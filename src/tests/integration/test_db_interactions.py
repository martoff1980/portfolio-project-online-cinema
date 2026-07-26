import uuid
import pytest
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from src.models.auth import User, UserGroup, UserGroupEnum
from src.models.movies import Movie, Genre, Certification
from src.models.orders import Order, OrderItem, OrderStatusEnum
from src.models.cart import Cart, CartItem


@pytest.mark.asyncio
class TestUserDatabaseInteractions:
    """Integration of the user entity and roles with the database."""

    async def test_create_user_with_role(self, db_session: AsyncSession):
        """Verification of successful user creation linked to a role."""
        # Retrieve the USER role from the predefined data.
        query = select(UserGroup).where(UserGroup.name == UserGroupEnum.USER)
        result = await db_session.execute(query)
        user_role = result.scalar_one()

        # Create user
        user = User(
            email="db_test_user@cinema.com",
            hashed_password="hashed_secret_password_123",
            group_id=user_role.id,
            is_active=True
        )
        db_session.add(user)
        await db_session.commit()
        await db_session.refresh(user)

        # Check record in DB
        assert user.id is not None
        assert user.email == "db_test_user@cinema.com"
        assert user.group.name == UserGroupEnum.USER

    async def test_user_unique_email_constraint(
        self, db_session: AsyncSession
    ):
        """
        The database must raise an IntegrityError
        when attempting to duplicate an email.
        """
        # Get any group
        query = select(UserGroup).where(UserGroup.name == UserGroupEnum.USER)
        result = await db_session.execute(query)
        user_role = result.scalar_one()

        user1 = User(
            email="unique@cinema.com",
            hashed_password="pass",
            group_id=user_role.id
        )
        user2 = User(
            email="unique@cinema.com",
            hashed_password="pass",
            group_id=user_role.id
        )

        db_session.add(user1)
        await db_session.commit()

        # Try add another user with same email
        db_session.add(user2)
        with pytest.raises(IntegrityError):
            await db_session.commit()

        await db_session.rollback()


@pytest.mark.asyncio
class TestMovieAndGenreInteractions:
    """Testing many-to-many relationships between movies and genres."""

    async def test_create_movie_with_genres(self, db_session: AsyncSession):
        """Creating a film that blends multiple genres."""
        # Create genres
        genre_sci_fi = Genre(name="Sci-Fi")
        genre_drama = Genre(name="Drama")
        db_session.add_all([genre_sci_fi, genre_drama])

        certification = Certification(name="PG-13")
        db_session.add(certification)

        await db_session.commit()

        # Create movie and linked genre
        movie = Movie(
            uuid=str(uuid.uuid4()),
            name="Inception",
            description="A thief who steals corporate secrets "
                        "through dream-sharing technology.",
            price=19.99,
            year=2010,
            time=148,
            imdb=6.8,
            certification_id=certification.id,
            genres=[genre_sci_fi, genre_drama]
        )
        db_session.add(movie)
        await db_session.commit()
        await db_session.refresh(
            movie, attribute_names=["genres"]
        )

        # Check link Many-to-Many
        assert movie.id is not None
        assert len(movie.genres) == 2
        genre_names = [g.name for g in movie.genres]
        assert "Sci-Fi" in genre_names
        assert "Drama" in genre_names


@pytest.mark.asyncio
class TestCartAndOrdersCascadeInteractions:
    """
    Testing cascade deletion and
    relationship overloading for Carts and Orders.
    """

    async def test_cart_item_cascade_delete_on_user_delete(
        self, db_session: AsyncSession
    ):
        """
        When a user is deleted,
        their cart and the items in the cart must be deleted
        via a cascade operation.
        """
        # Create role
        result = await db_session.execute(
            select(UserGroup).where(UserGroup.name == UserGroupEnum.USER)
        )
        user_role = result.scalar_one()

        # Create user, movie and add items into cart
        user = User(
            email="cascade_test@cinema.com",
            hashed_password="pass",
            group_id=user_role.id
        )

        certification = Certification(name="PG-13")
        db_session.add(certification)
        await db_session.commit()

        movie = Movie(
            uuid=str(uuid.uuid4()),
            name="Matrix",
            description="Test",
            price=12.00,
            year=1999,
            time=136,
            imdb=6.8,
            certification_id=certification.id,
        )
        db_session.add_all([user, movie])
        await db_session.commit()

        cart = Cart(user_id=user.id)
        db_session.add(cart)
        await db_session.commit()

        cart_item = CartItem(cart_id=cart.id, movie_id=movie.id)
        db_session.add(cart_item)
        await db_session.commit()

        #  Delete user
        await db_session.delete(user)
        await db_session.commit()

        # Verify that the cart and cart items
        # have been removed from the database.
        cart_check = await db_session.get(Cart, cart.id)
        cart_item_check = await db_session.get(CartItem, cart_item.id)

        assert cart_check is None
        assert cart_item_check is None

    async def test_create_order_with_items_and_status(
        self, db_session: AsyncSession
    ):
        """
        Test for saving an order and the associated
        OrderItem table to the database.
        """
        # Create user and movie
        result = await db_session.execute(
            select(UserGroup).where(UserGroup.name == UserGroupEnum.USER)
        )
        user_role = result.scalar_one()

        certification = Certification(name="PG-13")
        db_session.add(certification)
        await db_session.commit()

        user = User(
            email="order_db_test@cinema.com",
            hashed_password="pass",
            group_id=user_role.id
        )
        movie = Movie(
            uuid=str(uuid.uuid4()),
            name="Dune",
            description="Test Dune",
            price=15.00,
            year=2021,
            time=155,
            imdb=6.8,
            certification_id=certification.id,
        )
        db_session.add_all([user, movie])
        await db_session.commit()

        # Create order
        order = Order(
            user_id=user.id,
            total_amount=15.00,
            status=OrderStatusEnum.PENDING
        )
        db_session.add(order)
        await db_session.commit()

        order_item = OrderItem(
            order_id=order.id,
            movie_id=movie.id,
            price_at_order=15.00
        )
        db_session.add(order_item)
        await db_session.commit()

        # Retrieve data from the database using Eager/Select JOIN
        # and verify integrity.
        stmt = (
            select(Order)
            .options(selectinload(Order.items))
            .where(Order.id == order.id)
        )
        res = await db_session.execute(stmt)
        fetched_order = res.scalar_one()

        assert fetched_order.status == OrderStatusEnum.PENDING
        assert fetched_order.total_amount == 15.00
        assert len(fetched_order.items) == 1
        assert fetched_order.items[0].movie_id == movie.id
