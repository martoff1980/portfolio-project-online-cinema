from pydantic import BaseModel, Field, condecimal
from typing import List, Optional
from datetime import datetime

class GenreSchema(BaseModel):
    id: int
    name: str

    class Config:
        from_attributes = True

class StarSchema(BaseModel):
    id: int
    name: str

    class Config:
        from_attributes = True

class DirectorSchema(BaseModel):
    id: int
    name: str

    class Config:
        from_attributes = True

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

    class Config:
        from_attributes = True

class CommentCreate(BaseModel):
    text: str = Field(..., min_length=1)
    parent_id: Optional[int] = None

class CommentResponse(BaseModel):
    id: int
    user_id: int
    movie_id: int
    text: str
    parent_id: Optional[int]
    created_at: datetime

    class Config:
        from_attributes = True

class RatingCreate(BaseModel):
    rating: int = Field(..., ge=1, le=10)