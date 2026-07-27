from typing import List, Set
from src.exceptions import DuplicatePurchaseException


class CartService:
    """Business logic service for the shopping cart."""

    @staticmethod
    def calculate_total(cart_items: List) -> float:
        """
        A pure function for calculating the total cost of items
        in the shopping cart.
        """
        if not cart_items:
            return 0.00
        return float(sum(item.movie.price for item in cart_items))

    @staticmethod
    def validate_movie_addition(
        user_id: int,
        movie_id: int,
        owned_movie_ids: Set[int]
    ) -> None:
        """
        Business rule: preventing the repurchase of a movie.
        """
        if movie_id in owned_movie_ids:
            raise DuplicatePurchaseException(
                detail="You already own this movie"
            )
