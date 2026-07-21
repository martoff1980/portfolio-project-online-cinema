from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from src.models.movies import (
    Comment,
    Movie,
    MovieLike,
    FavoriteMovie,
    MovieRating
)
from src.schemas.movies import CommentCreate, CommentResponse, RatingCreate
from src.dependencies import get_current_user
from src.database import get_db

router = APIRouter()


# Write comment to a movie.
@router.post("/{movie_id}/comments", response_model=CommentResponse)
async def add_comment(
    movie_id: int,
    payload: CommentCreate,
    db: AsyncSession = Depends(get_db),
    user=Depends(get_current_user),
):
    movie = await db.get(Movie, movie_id)
    if not movie:
        raise HTTPException(status_code=404, detail="Movie not found.")

    comment = Comment(
        user_id=user.id,
        movie_id=movie_id,
        text=payload.text,
        parent_id=payload.parent_id,
    )
    db.add(comment)
    await db.commit()
    await db.refresh(comment)

    return comment


# Like / Dislike
@router.post("/{movie_id}/like")
async def toggle_like(
    movie_id: int,
    # True = like, False = dislike
    is_like: bool,
    db: AsyncSession = Depends(get_db),
    user=Depends(get_current_user),
):
    # Check if the user has already rated the movie
    stmt = select(MovieLike).where(
        MovieLike.user_id == user.id, MovieLike.movie_id == movie_id
    )
    like_record = (await db.execute(stmt)).scalars().first()

    if like_record:
        if like_record.is_like == is_like:
            # If the user clicks the same reaction again,
            # remove it (toggle off)
            await db.delete(like_record)
            message = "Reaction removed."
        else:
            # Check if the user has already rated the movie
            like_record.is_like = is_like
            message = "Reaction updated."
    else:
        # New reaction
        new_reaction = MovieLike(
            user_id=user.id,
            movie_id=movie_id,
            is_like=is_like
        )
        db.add(new_reaction)
        message = "Reaction added."

    await db.commit()
    return {"message": message}


# --- Поставить оценку (1-10 звезд) ---
# Mark (1-10 stars)
@router.post("/{movie_id}/rate")
async def rate_movie(
    movie_id: int,
    payload: RatingCreate,
    db: AsyncSession = Depends(get_db),
    user=Depends(get_current_user),
):
    stmt = select(MovieRating).where(
        MovieRating.user_id == user.id, MovieRating.movie_id == movie_id
    )
    rating_record = (await db.execute(stmt)).scalars().first()

    if rating_record:
        rating_record.rating = payload.rating
    else:
        rating_record = MovieRating(
            user_id=user.id, movie_id=movie_id, rating=payload.rating
        )
        db.add(rating_record)

    await db.commit()
    return {"message": f"Successfully rated {payload.rating}/10."}


# Add / Remove from favorites
@router.post("/{movie_id}/favorite")
async def toggle_favorite(
    movie_id: int,
    db: AsyncSession = Depends(get_db),
    user=Depends(get_current_user)
):
    stmt = select(FavoriteMovie).where(
        FavoriteMovie.user_id == user.id, FavoriteMovie.movie_id == movie_id
    )
    fav_record = (await db.execute(stmt)).scalars().first()

    if fav_record:
        await db.delete(fav_record)
        message = "Removed from favorites."
    else:
        db.add(FavoriteMovie(user_id=user.id, movie_id=movie_id))
        message = "Added to favorites."

    await db.commit()
    return {"message": message}
