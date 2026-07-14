from src.models.movies import Comment, MovieLike, FavoriteMovie, MovieRating
from src.schemas.movies import CommentCreate, CommentResponse, RatingCreate
from src.dependencies import get_current_user

# --- Написать коммент к фильму ---
@router.post("/{movie_id}/comments", response_model=CommentResponse)
async def add_comment(
    movie_id: int,
    payload: CommentCreate,
    db: AsyncSession = Depends(get_db),
    user = Depends(get_current_user)
):
    movie = await db.get(Movie, movie_id)
    if not movie:
        raise HTTPException(status_code=404, detail="Movie not found.")

    comment = Comment(
        user_id=user.id,
        movie_id=movie_id,
        text=payload.text,
        parent_id=payload.parent_id
    )
    db.add(comment)
    await db.commit()
    await db.refresh(comment)

    # Логика нотификации: Если parent_id не None, то нужно уведомить автора родительского коммента
    # Это можно запустить как фоновую задачу Celery.

    return comment


# --- Поставить лайк / дизлайк ---
@router.post("/{movie_id}/like")
async def toggle_like(
    movie_id: int,
    is_like: bool,  # True = like, False = dislike
    db: AsyncSession = Depends(get_db),
    user = Depends(get_current_user)
):
    # Проверяем, оценивал ли юзер фильм ранее
    stmt = select(MovieLike).where(MovieLike.user_id == user.id, MovieLike.movie_id == movie_id)
    like_record = (await db.execute(stmt)).scalars().first()

    if like_record:
        if like_record.is_like == is_like:
            # Если кликнули то же самое — убираем оценку (Toggle)
            await db.delete(like_record)
            message = "Reaction removed."
        else:
            # Меняем лайк на дизлайк или наоборот
            like_record.is_like = is_like
            message = "Reaction updated."
    else:
        # Ставим новую оценку
        new_reaction = MovieLike(user_id=user.id, movie_id=movie_id, is_like=is_like)
        db.add(new_reaction)
        message = "Reaction added."

    await db.commit()
    return {"message": message}


# --- Поставить оценку (1-10 звезд) ---
@router.post("/{movie_id}/rate")
async def rate_movie(
    movie_id: int,
    payload: RatingCreate,
    db: AsyncSession = Depends(get_db),
    user = Depends(get_current_user)
):
    stmt = select(MovieRating).where(MovieRating.user_id == user.id, MovieRating.movie_id == movie_id)
    rating_record = (await db.execute(stmt)).scalars().first()

    if rating_record:
        rating_record.rating = payload.rating
    else:
        rating_record = MovieRating(user_id=user.id, movie_id=movie_id, rating=payload.rating)
        db.add(rating_record)

    await db.commit()
    return {"message": f"Successfully rated {payload.rating}/10."}


# --- Добавить / Удалить из избранного ---
@router.post("/{movie_id}/favorite")
async def toggle_favorite(
    movie_id: int,
    db: AsyncSession = Depends(get_db),
    user = Depends(get_current_user)
):
    stmt = select(FavoriteMovie).where(FavoriteMovie.user_id == user.id, FavoriteMovie.movie_id == movie_id)
    fav_record = (await db.execute(stmt)).scalars().first()

    if fav_record:
        await db.delete(fav_record)
        message = "Removed from favorites."
    else:
        db.add(FavoriteMovie(user_id=user.id, movie_id=movie_id))
        message = "Added to favorites."

    await db.commit()
    return {"message": message}