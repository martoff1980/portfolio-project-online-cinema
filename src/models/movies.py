from typing import List, Optional
from datetime import datetime
from sqlalchemy import Table, Column, Integer, ForeignKey, String, Float, Decimal, DateTime, UniqueConstraint, CheckConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship
from src.models.auth import Base, User
# --- Ассоциативные таблицы для связей Многие-ко-Многим ---

movie_genres = Table(
    "movie_genres",
    Base.metadata,
    Column("movie_id", Integer, ForeignKey("movies.id", ondelete="CASCADE"), primary_key=True),
    Column("genre_id", Integer, ForeignKey("genres.id", ondelete="CASCADE"), primary_key=True),
)

movie_directors = Table(
    "movie_directors",
    Base.metadata,
    Column("movie_id", Integer, ForeignKey("movies.id", ondelete="CASCADE"), primary_key=True),
    Column("director_id", Integer, ForeignKey("directors.id", ondelete="CASCADE"), primary_key=True),
)

movie_stars = Table(
    "movie_stars",
    Base.metadata,
    Column("movie_id", Integer, ForeignKey("movies.id", ondelete="CASCADE"), primary_key=True),
    Column("star_id", Integer, ForeignKey("stars.id", ondelete="CASCADE"), primary_key=True),
)

# --- Основные сущности ---

class Genre(Base):
    __tablename__ = "genres"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String, unique=True, nullable=False)

    movies: Mapped[List["Movie"]] = relationship(
        "Movie", secondary=movie_genres, back_populates="genres"
    )


class Star(Base):
    __tablename__ = "stars"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String, unique=True, nullable=False)

    movies: Mapped[List["Movie"]] = relationship(
        "Movie", secondary=movie_stars, back_populates="stars"
    )


class Director(Base):
    __tablename__ = "directors"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String, unique=True, nullable=False)

    movies: Mapped[List["Movie"]] = relationship(
        "Movie", secondary=movie_directors, back_populates="directors"
    )


class Certification(Base):
    __tablename__ = "certifications"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String, unique=True, nullable=False)

    movies: Mapped[List["Movie"]] = relationship("Movie", back_populates="certification")


class Movie(Base):
    __tablename__ = "movies"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    uuid: Mapped[str] = mapped_column(String, unique=True, nullable=False)  # Генерируется на уровне приложения/БД
    name: Mapped[str] = mapped_column(String, nullable=False)
    year: Mapped[int] = mapped_column(Integer, nullable=False)
    time: Mapped[int] = mapped_column(Integer, nullable=False)  # Продолжительность в минутах
    imdb: Mapped[float] = mapped_column(Float, nullable=False)
    votes: Mapped[int] = mapped_column(Integer, default=0)
    meta_score: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    gross: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    description: Mapped[str] = mapped_column(String, nullable=False)
    price: Mapped[Decimal] = mapped_column(Decimal(10, 2), nullable=False)
    certification_id: Mapped[int] = mapped_column(ForeignKey("certifications.id"), nullable=False)

    # Ограничение уникальности на комбинацию (название, год, длительность)
    __table_args__ = (
        UniqueConstraint("name", "year", "time", name="uq_movie_name_year_time"),
    )

    # Отношения
    certification: Mapped["Certification"] = relationship("Certification", back_populates="movies")
    genres: Mapped[List["Genre"]] = relationship("Genre", secondary=movie_genres, back_populates="movies")
    directors: Mapped[List["Director"]] = relationship("Director", secondary=movie_directors, back_populates="movies")
    stars: Mapped[List["Star"]] = relationship("Star", secondary=movie_stars, back_populates="movies")
    
    comments: Mapped[List["Comment"]] = relationship("Comment", back_populates="movie", cascade="all, delete-orphan")
    likes: Mapped[List["MovieLike"]] = relationship("MovieLike", back_populates="movie", cascade="all, delete-orphan")
    ratings: Mapped[List["MovieRating"]] = relationship("MovieRating", back_populates="movie", cascade="all, delete-orphan")
    favorites: Mapped[List["FavoriteMovie"]] = relationship("FavoriteMovie", back_populates="movie", cascade="all, delete-orphan")


# --- Новые сущности: Лайки, Избранное, Комментарии, Рейтинги ---

class MovieLike(Base):
    __tablename__ = "movie_likes"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    movie_id: Mapped[int] = mapped_column(ForeignKey("movies.id", ondelete="CASCADE"), nullable=False)
    is_like: Mapped[bool] = mapped_column(Boolean, nullable=False)  # True = Like, False = Dislike
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    __table_args__ = (
        UniqueConstraint("user_id", "movie_id", name="uq_user_movie_like"),
    )

    movie: Mapped["Movie"] = relationship("Movie", back_populates="likes")


class FavoriteMovie(Base):
    __tablename__ = "favorite_movies"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    movie_id: Mapped[int] = mapped_column(ForeignKey("movies.id", ondelete="CASCADE"), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    __table_args__ = (
        UniqueConstraint("user_id", "movie_id", name="uq_user_movie_favorite"),
    )

    movie: Mapped["Movie"] = relationship("Movie", back_populates="favorites")


class Comment(Base):
    __tablename__ = "comments"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    movie_id: Mapped[int] = mapped_column(ForeignKey("movies.id", ondelete="CASCADE"), nullable=False)
    text: Mapped[str] = mapped_column(String, nullable=False)
    parent_id: Mapped[Optional[int]] = mapped_column(ForeignKey("comments.id", ondelete="CASCADE"), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    movie: Mapped["Movie"] = relationship("Movie", back_populates="comments")
    replies: Mapped[List["Comment"]] = relationship("Comment", cascade="all, delete-orphan")


class MovieRating(Base):
    __tablename__ = "movie_ratings"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    movie_id: Mapped[int] = mapped_column(ForeignKey("movies.id", ondelete="CASCADE"), nullable=False)
    rating: Mapped[int] = mapped_column(Integer, nullable=False)  # От 1 до 10

    __table_args__ = (
        UniqueConstraint("user_id", "movie_id", name="uq_user_movie_rating"),
        CheckConstraint("rating >= 1 AND rating <= 10", name="chk_rating_range"),
    )

    movie: Mapped["Movie"] = relationship("Movie", back_populates="ratings")