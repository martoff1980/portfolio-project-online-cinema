import pytest
from pydantic import ValidationError

from src.schemas.movies import MovieCreate, MovieFilter


class TestMovieValidation:
    """
    Validation of movie schemas and filtering parameters.
    """

    def test_movie_create_schema_valid(self):
        """
        Verification of a valid film creation scheme.
        """
        data = {
            "name": "Interstellar",
            "description":
                "A team of explorers travel through a wormhole in space.",
            "price": 14.99,
            "year": 2014,
            "time": 169,
            "imdb": 8.7,
            "certification_id": 1,
            "genre_ids": [1, 2],
            "director_ids": [10],
            "star_ids": [100, 101],
        }

        movie = MovieCreate(**data)
        assert movie.price == 14.99
        assert movie.year == 2014

    def test_movie_create_schema_negative_price(self):
        """
        The price of the film cannot be negative or zero.
        """
        with pytest.raises(ValidationError) as exc_info:
            MovieCreate(
                name="Free Movie",
                description="Some description",
                price=-5.0,
                year=2024,
                time=120
            )
        assert "price" in str(exc_info.value)

    def test_movie_filter_schema_sorting_validation(self):
        """
        Verification of sorting validation in catalog filters.

        """
        # An invalid sorting field must trigger an error.
        with pytest.raises(ValidationError):
            MovieFilter(sort_by="invalid_column_name")

        # Permissible field and direction
        valid_filter = MovieFilter(sort_by="price", order="desc")
        assert valid_filter.sort_by == "price"
        assert valid_filter.order == "desc"


class TestMovieFilterValidation:
    """
    Validation of the movie catalog filtering and pagination schema.
    """

    def test_movie_filter_schema_defaults(self):
        """
        Verifying default values ​​for pagination and sorting.
        """
        filters = MovieFilter()
        assert filters.page == 1
        assert filters.limit == 10
        assert filters.sort_by == "created_at"
        assert filters.order == "desc"

    def test_movie_filter_schema_valid_custom_params(self):
        """
        Verification of valid filter transmission.
        """
        filters = MovieFilter(
            genre="Sci-Fi",
            min_price=10.0,
            max_price=20.0,
            sort_by="price",
            order="asc",
            page=2,
            limit=20
        )
        assert filters.genre == "Sci-Fi"
        assert filters.min_price == 10.0
        assert filters.max_price == 20.0
        assert filters.sort_by == "price"

    def test_movie_filter_schema_invalid_sort_by(self):
        """
        Checking for an error regarding a non-existent sorting field.
        """
        with pytest.raises(ValidationError) as exc_info:
            MovieFilter(sort_by="invalid_column_name")
        assert "sort_by" in str(exc_info.value)

    def test_movie_filter_schema_invalid_price_range(self):
        """
        max_price cannot be less than min_price.
        """
        with pytest.raises(ValidationError) as exc_info:
            MovieFilter(min_price=50.0, max_price=10.0)
        assert "max_price" in str(exc_info.value)

    def test_movie_filter_schema_negative_page_or_limit(self):
        """
        The page number and limit must be positive numbers.
        """
        with pytest.raises(ValidationError):
            MovieFilter(page=0)

        with pytest.raises(ValidationError):
            MovieFilter(limit=150)
