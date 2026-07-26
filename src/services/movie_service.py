from typing import Sequence, Dict, Any
from sqlalchemy import select, asc, desc
from sqlalchemy.orm import selectinload
from sqlalchemy.ext.asyncio import AsyncSession

from src.models.movies import Movie, Genre
from src.schemas.movies import MovieFilter


class MovieService:
    """
    A service for managing a movie catalog (CRUD, filtering, sorting).
    """

    @staticmethod
    async def get_filtered_movies(
        db_session: AsyncSession,
        filters: MovieFilter
    ) -> Sequence[Movie]:
        """
        Returns a list of movies from the database based on the provided
        filtering, sorting, and pagination criteria.
        """
        # Base query with eager loading of genres (selectinload prevents N+1)
        query = select(Movie).options(selectinload(Movie.genres))

        # Filtering by genre (JOIN with the genres table)
        if filters.genre:
            query = query.join(Movie.genres).where(Genre.name.ilike(f"%{filters.genre}%"))

        # Search by name or description
        if filters.search:
            search_pattern = f"%{filters.search}%"
            query = query.where(
                Movie.name.ilike(search_pattern) | Movie.description.ilike(search_pattern)
            )

        # Band filters
        if filters.min_price is not None:
            query = query.where(Movie.price >= filters.min_price)

        if filters.max_price is not None:
            query = query.where(Movie.price <= filters.max_price)

        if filters.year is not None:
            query = query.where(Movie.year == filters.year)

        # Sorted
        # sort_column = getattr(Movie, filters.sort_by, Movie.created_at)
        sort_fields: Dict[str, Any] = {
            "price": Movie.price,
            "year": Movie.year,
            "ratings": Movie.ratings,
            "name": Movie.name,
        }
        sort_column = sort_fields.get(filters.sort_by or "", Movie.id)

        if filters.order == "asc":
            query = query.order_by(asc(sort_column))
        else:
            query = query.order_by(desc(sort_column))

        # 6. Пагинация (OFFSET & LIMIT)
        offset = (filters.page - 1) * filters.limit
        query = query.offset(offset).limit(filters.limit)

        # 7. Выполнение запроса
        result = await db_session.execute(query)

        # unique() требуется при работе с JOIN и selectinload в SQLAlchemy
        return result.scalars().unique().all()
