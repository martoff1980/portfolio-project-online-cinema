from pydantic import BaseModel, Field, ConfigDict, field_validator
from typing import List, Optional, Literal
from datetime import datetime


class GenreSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str


class StarSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str


class DirectorSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str


class MovieCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    year: int = Field(..., ge=1888, le=2100)
    time: int = Field(..., description="Duration in minutes", gt=0)
    imdb: float = Field(..., ge=0.0, le=10.0)
    description: str
    price: float = Field(..., gt=0.0)
    certification_id: int
    genre_ids: List[int]
    director_ids: List[int]
    star_ids: List[int]


class MovieResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    uuid: str
    name: str
    year: int
    time: int
    imdb: float
    votes: int
    description: str
    price: float
    genres: List[GenreSchema]
    directors: List[DirectorSchema]
    stars: List[StarSchema]


class CommentCreate(BaseModel):
    text: str = Field(..., min_length=1)
    parent_id: Optional[int] = None


class CommentResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    user_id: int
    movie_id: int
    text: str
    parent_id: Optional[int]
    created_at: datetime


class RatingCreate(BaseModel):
    rating: int = Field(..., ge=1, le=10)


class MovieFilter(BaseModel):
    """
    Schema for validating filtering, search, sorting,
    and pagination parameters for the movie catalog.
    """
    genre: Optional[str] = Field(
        None,
        description="Filter by genre name"
    )
    search: Optional[str] = Field(
        None,
        description="Search by movie title or description"
    )
    min_price: Optional[float] = Field(
        None,
        ge=0,
        description="Minimum price (>= 0)")
    max_price: Optional[float] = Field(
        None,
        ge=0,
        description="Maximum price (>= 0)"
    )
    year: Optional[int] = Field(
        None,
        ge=1888,
        description="Film release year"
    )

    # Sorting: only existing fields of the movies table are allowed.
    sort_by: Optional[
        Literal["price", "year", "rating", "created_at", "name"]
        ] = Field(
        "created_at", description="Sorting field"
    )
    order: Optional[Literal["asc", "desc"]] = Field(
        "desc",
        description="Sorting direction (asc – ascending, desc – descending)"
    )

    # Pagination
    page: int = Field(1, ge=1, description="Page number (starting from 1)")
    limit: int = Field(
        10,
        ge=1,
        le=100,
        description="Number of items per page (maximum 100)"
    )

    @field_validator("max_price")
    @classmethod
    def validate_price_range(
        cls,
        max_price: Optional[float],
        info
    ) -> Optional[float]:
        """
        Business rule check: max_price must not be less than min_price.
        """
        min_price = info.data.get("min_price")
        if (
            min_price is not None
            and max_price is not None
            and max_price < min_price
        ):
            raise ValueError("max_price cannot be less than min_price")
        return max_price


class GenreRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    """Schema for reading genre data."""
    id: int
    name: str


class MovieRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    """Schema for representing movie information in the API."""
    id: int
    name: str
    description: Optional[str] = None
    price: float
    year: int
    time: int
    rating: Optional[float] = 0.0
    created_at: Optional[datetime] = None
    genres: List[GenreRead] = []
