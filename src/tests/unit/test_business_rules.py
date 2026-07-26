import pytest
from unittest.mock import MagicMock
from fastapi import status, HTTPException

from src.models.auth import UserGroupEnum, User
from src.models.movies import Movie
from src.models.orders import Order, OrderStatusEnum
from src.services.cart_service import CartService
from src.services.order_service import OrderService
from src.exceptions import (
    DuplicatePurchaseException,
    PermissionDeniedException,
    CinemaException
)


class TestBusinessRulesCalculation:
    """
    Testing calculated business rules (prices, shopping cart, totals).
    """

    def test_calculate_cart_total_price(self):
        """Verification of the total cart amount calculation."""
        # Creating test movie objects using MagicMock/Dataclass
        movie1 = MagicMock(spec=Movie, id=1, price=10.00)
        movie2 = MagicMock(spec=Movie, id=2, price=25.50)
        movie3 = MagicMock(spec=Movie, id=3, price=14.50)

        cart_items = [
            MagicMock(movie=movie1),
            MagicMock(movie=movie2),
            MagicMock(movie=movie3),
        ]

        # Call the pure price calculation method
        total_price = CartService.calculate_total(cart_items)
        assert total_price == 50.00

    def test_empty_cart_total_is_zero(self):
        """The total for an empty cart must be 0.00."""
        total_price = CartService.calculate_total([])
        assert total_price == 0.00


class TestDuplicatePurchasePreventionRule:
    """
    Testing the business rule:
    prohibition on re-purchasing a previously purchased movie.
    """

    def test_prevent_adding_already_owned_movie_to_cart(self):
        """
        Business rule:
        If the user already owns the movie (active purchase),
        the system must throw a DuplicatePurchaseException when
        attempting to add it to the cart.
        """
        user_id = 100
        movie_id = 5

        # List of movie IDs already owned by the user
        owned_movie_ids = {1, 3, 5, 8}

        # Verify that the business service blocks the addition
        with pytest.raises(DuplicatePurchaseException) as exc_info:
            CartService.validate_movie_addition(
                user_id=user_id,
                movie_id=movie_id,
                owned_movie_ids=owned_movie_ids
            )

        assert "You already own this movie" in str(exc_info.value)

    def test_allow_adding_unowned_movie_to_cart(self):
        """
        Allow adding the movie to the cart if the user does not already own it.
        """
        owned_movie_ids = {1, 3, 8}
        # The movie is not in the list of purchased items
        movie_id_to_buy = 5

        # Should not throw exceptions
        CartService.validate_movie_addition(
            user_id=100,
            movie_id=movie_id_to_buy,
            owned_movie_ids=owned_movie_ids
        )


class TestRBACBusinessRules:
    """Testing access control rules (Role-Based Access Control)."""

    def test_user_cannot_access_admin_panel_logic(self):
        """
        A user with the USER role does not have moderation
        or administration rights.
        """
        regular_user = MagicMock(
            spec=User, group=MagicMock(name=UserGroupEnum.USER)
        )

        # Access business rule check
        is_allowed = OrderService.can_cancel_any_order(user=regular_user)
        assert is_allowed is False

    def test_admin_can_access_admin_panel_logic(self):
        """A user with the ADMIN role has full privileges."""
        admin_user = MagicMock(group=UserGroupEnum.ADMIN)
        is_allowed = OrderService.can_cancel_any_order(admin_user)
        assert is_allowed is True


class TestOrderStatusTransitionRules:
    """Testing valid transitions between order statuses."""

    def test_pending_order_can_be_paid(self):
        """
        An order with the status PENDING can transition to PAID.
        """
        order = MagicMock(spec=Order, status=OrderStatusEnum.PENDING)

        # Transition to the PAID status is permitted.
        OrderService.validate_status_transition(
            order, target_status=OrderStatusEnum.PAID
        )

    def test_paid_order_cannot_be_paid_again(self):
        """
        An order that has already been paid for (PAID)
        cannot be paid for again.
        """
        order = MagicMock(spec=Order, status=OrderStatusEnum.PAID)

        with pytest.raises(ValueError) as exc_info:
            OrderService.validate_status_transition(
                order,
                target_status=OrderStatusEnum.PAID
            )

        assert "Order is already paid" in str(exc_info.value)


class TestPermissionDeniedException:
    """Unit tests for the PermissionDeniedException."""

    def test_permission_denied_exception_default_values(self):
        """Verification of default values ​​(403 status and standard text)."""
        exc = PermissionDeniedException()

        assert exc.status_code == status.HTTP_403_FORBIDDEN
        assert exc.detail == "Permission denied"
        # Checking the inheritance hierarchy
        assert isinstance(exc, CinemaException)
        assert isinstance(exc, HTTPException)

    def test_permission_denied_exception_custom_message(self):
        """
        Verification of the transmission of a user-defined error message.
        """
        custom_message = "Only admins can perform this action"
        exc = PermissionDeniedException(detail=custom_message)

        assert exc.status_code == status.HTTP_403_FORBIDDEN
        assert exc.detail == custom_message

    def test_permission_denied_exception_raises(self):
        """
        Verifying correct exception raising using pytest.raises.
        """
        def dummy_admin_only_function():
            raise PermissionDeniedException(detail="Access restricted")

        with pytest.raises(PermissionDeniedException) as exc_info:
            dummy_admin_only_function()

        assert exc_info.value.status_code == 403
        assert exc_info.value.detail == "Access restricted"
