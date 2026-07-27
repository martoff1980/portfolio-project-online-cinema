import pytest
from pydantic import ValidationError

from src.schemas.cart import CartItemAdd


class TestCartValidation:
    """Shopping cart validation."""

    def test_cart_item_schema_positive_movie_id(self):
        """The movie ID must be a positive integer."""
        with pytest.raises(ValidationError):
            CartItemAdd(movie_id=-1)

        item = CartItemAdd(movie_id=42)
        assert item.movie_id == 42
