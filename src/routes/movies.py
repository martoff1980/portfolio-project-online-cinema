import uuid
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from database import get_db
from models import Movie, Genre, Director, Star, UserGroupEnum
from schemas import MovieCreate, MovieResponse
from dependencies import allow_moderator_or_admin

router = APIRouter(prefix="/movies", tags=["Movies Catalog"])

@router.post("/", response_model=MovieResponse, status_code=status.HTTP_201_CREATED)
async def create_movie(
    payload: MovieCreate,
    db: AsyncSession = Depends(get_db),
    current_user = Depends(allow_moderator_or_admin)  # Только Модератор или Админ
):
    # Проверяем уникальность по (name, year, time)
    stmt = select(Movie).where(
        Movie.name == payload.name,
        Movie.year == payload.year,
        Movie.time == payload.time
    )
    existing = (await db.execute(stmt)).scalars().first()
    if existing:
        raise HTTPException(
            status_code=400, 
            detail="Movie with this title, year and duration already exists."
        )

    # Создаем объект фильма
    new_movie = Movie(
        uuid=str(uuid.uuid4()),
        name=payload.name,
        year=payload.year,
        time=payload.time,
        imdb=payload.imdb,
        description=payload.description,
        price=payload.price,
        certification_id=payload.certification_id
    )

    # Навешиваем связи (Жанры, Директора, Актеры)
    if payload.genre_ids:
        genres_db = await db.execute(select(Genre).where(Genre.id.in_(payload.genre_ids)))
        new_movie.genres = list(genres_db.scalars().all())

    if payload.director_ids:
        directors_db = await db.execute(select(Director).where(Director.id.in_(payload.director_ids)))
        new_movie.directors = list(directors_db.scalars().all())

    if payload.star_ids:
        stars_db = await db.execute(select(Star).where(Star.id.in_(payload.star_ids)))
        new_movie.stars = list(stars_db.scalars().all())

    db.add(new_movie)
    await db.commit()
    await db.refresh(new_movie)
    return new_movie


@router.delete("/{movie_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_movie(
    movie_id: int,
    db: AsyncSession = Depends(get_db),
    current_user = Depends(allow_moderator_or_admin)
):
    movie = await db.get(Movie, movie_id)
    if not movie:
        raise HTTPException(status_code=404, detail="Movie not found.")

    # Проверка бизнес-логики: Запретить удаление, если фильм куплен хотя бы одним юзером.
    # (Эта часть будет полностью увязана на Шаге 4, когда появится таблица Order/OrderItem)
    # Псевдокод проверки:
    # is_purchased = await db.execute(select(OrderItem).where(OrderItem.movie_id == movie_id))
    # if is_purchased.first():
    #     raise HTTPException(status_code=400, detail="Cannot delete movie: it has already been purchased.")

    await db.delete(movie)
    await db.commit()
    return None