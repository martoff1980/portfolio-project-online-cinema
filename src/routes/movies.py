import uuid
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.database import get_db
from src.models.movies import Movie, Genre, Director, Star
from src.schemas.movies import MovieCreate, MovieResponse
from src.dependencies import allow_moderator_or_admin

router = APIRouter(prefix="/movies", tags=["Movies Catalog"])


@router.post(
    "/",
    response_model=MovieResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Add a new movie to the catalog",
    description="Allows moderators and administrators to add new movies. "
                "Checks the uniqueness of the combination of the film's title,"
                " release year, and duration.",
    responses={
        201: {"description": "The film has been successfully created."},
        400: {
            "description":
                "A film with these parameters already exists in the database."
        },
        401: {"description": "User not authorized (invalid token)."},
        403: {
            "description":
                "Insufficient permissions (available only to MODERATOR/ADMIN)."
        },
    },
)
@router.post(
    "/",
    response_model=MovieResponse,
    status_code=status.HTTP_201_CREATED
)
async def create_movie(
    payload: MovieCreate,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(allow_moderator_or_admin),
):
    # Check if a movie with the same
    # name, year, and time already exists
    stmt = select(Movie).where(
        Movie.name == payload.name,
        Movie.year == payload.year,
        Movie.time == payload.time,
    )
    existing = (await db.execute(stmt)).scalars().first()
    if existing:
        raise HTTPException(
            status_code=400,
            detail="Movie with this title, year and duration already exists.",
        )

    # Create a new movie
    new_movie = Movie(
        uuid=str(uuid.uuid4()),
        name=payload.name,
        year=payload.year,
        time=payload.time,
        imdb=payload.imdb,
        description=payload.description,
        price=payload.price,
        certification_id=payload.certification_id,
    )

    # link genres, directors,
    # and stars if their IDs are provided in the payload
    if payload.genre_ids:
        genres_db = await db.execute(
            select(Genre).where(Genre.id.in_(payload.genre_ids))
        )
        new_movie.genres = list(genres_db.scalars().all())

    if payload.director_ids:
        directors_db = await db.execute(
            select(Director).where(Director.id.in_(payload.director_ids))
        )
        new_movie.directors = list(directors_db.scalars().all())

    if payload.star_ids:
        stars_db = await db.execute(
            select(Star).where(Star.id.in_(payload.star_ids))
        )
        new_movie.stars = list(stars_db.scalars().all())

    db.add(new_movie)
    await db.commit()
    await db.refresh(new_movie)
    return new_movie


@router.delete("/{movie_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_movie(
    movie_id: int,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(allow_moderator_or_admin),
):
    movie = await db.get(Movie, movie_id)
    if not movie:
        raise HTTPException(status_code=404, detail="Movie not found.")

    await db.delete(movie)
    await db.commit()
    return None
