import uuid
from datetime import datetime, timedelta
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.database import get_db
from src.models.auth import (
    User,
    UserGroup,
    UserGroupEnum,
    ActivationToken,
    RefreshToken,
    UserProfile
)
from src.schemas.auth import (
    UserCreate,
    UserLogin,
    TokenResponse,
    RefreshTokenRequest,
    PasswordResetRequest
)
from src.security import (
    hash_password, verify_password, validate_password_complexity,
    create_access_token
)

router = APIRouter(prefix="/auth", tags=["Authentication"])


@router.post("/register", status_code=status.HTTP_201_CREATED)
async def register(payload: UserCreate, db: AsyncSession = Depends(get_db)):
    # 1. Проверяем сложность пароля
    validate_password_complexity(payload.password)

    # 2. Уникальность Email
    result = await db.execute(
        select(User).where(User.email == payload.email)
    )
    if result.scalars().first():
        raise HTTPException(
            status_code=400,
            detail="Email already registered."
        )

    # 3. Получение дефолтной роли USER
    group_result = await db.execute(
        select(UserGroup).where(UserGroup.name == UserGroupEnum.USER)
    )
    user_group = group_result.scalars().first()
    if not user_group:
        # Создаем группу, если вдруг нет в БД
        # (для стабильности при первом запуске)
        user_group = UserGroup(name=UserGroupEnum.USER)
        db.add(user_group)
        await db.flush()

    # 4. Создаем пользователя
    hashed = hash_password(payload.password)
    new_user = User(
        email=payload.email,
        hashed_password=hashed,
        is_active=False,
        group_id=user_group.id
    )
    db.add(new_user)
    await db.flush()

    # Создаем пустой профиль
    profile = UserProfile(user_id=new_user.id)
    db.add(profile)

    # 5. Генерация токена активации (на 24 часа)
    token_str = str(uuid.uuid4())
    activation = ActivationToken(
        user_id=new_user.id,
        token=token_str,
        expires_at=datetime.utcnow() + timedelta(hours=24)
    )
    db.add(activation)
    await db.commit()

    # Фоновая отправка email (заглушка или вызов Celery задачи)
    # send_activation_email.delay(new_user.email, token_str)

    return {
        "message":
            "Registration successful."
            "Please check your email to activate your account."
    }


@router.get("/activate/{token}")
async def activate_account(token: str, db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(ActivationToken).where(ActivationToken.token == token)
    )
    act_token = result.scalars().first()

    if not act_token:
        raise HTTPException(
            status_code=400,
            detail="Invalid token."
        )

    if act_token.expires_at < datetime.utcnow():
        raise HTTPException(
            status_code=400,
            detail="Activation token has expired."
        )

    # Активируем пользователя
    user_result = await db.execute(
        select(User).where(User.id == act_token.user_id)
    )
    user = user_result.scalars().first()
    if user:
        user.is_active = True

    # Удаляем токен
    await db.delete(act_token)
    await db.commit()

    return {"message": "Account successfully activated."}


@router.post("/resend-activation")
async def resend_activation(
    payload: PasswordResetRequest,
    db: AsyncSession = Depends(get_db)
):
    result = await db.execute(
        select(User).where(User.email == payload.email)
    )
    user = result.scalars().first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found.")

    if user.is_active:
        return {"message": "Account is already active."}

    # Удаляем старый токен, если он был
    token_result = await db.execute(
        select(ActivationToken).where(ActivationToken.user_id == user.id)
    )
    old_token = token_result.scalars().first()
    if old_token:
        await db.delete(old_token)
        await db.flush()

    # Новый токен на 24 часа
    new_token_str = str(uuid.uuid4())
    new_token = ActivationToken(
        user_id=user.id,
        token=new_token_str,
        expires_at=datetime.utcnow() + timedelta(hours=24)
    )
    db.add(new_token)
    await db.commit()

    # send_activation_email.delay(user.email, new_token_str)
    return {
        "message": "A new activation link has been sent to your email."
    }


@router.post("/login", response_model=TokenResponse)
async def login(payload: UserLogin, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(User).where(User.email == payload.email))
    user = result.scalars().first()

    if not user or not verify_password(payload.password, user.hashed_password):
        raise HTTPException(
            status_code=401,
            detail="Incorrect email or password."
        )

    if not user.is_active:
        raise HTTPException(
            status_code=400,
            detail="Account is not active. Please activate first."
        )

    # Генерируем access token
    access_token = create_access_token(data={"sub": str(user.id)})

    # Генерируем refresh token (uuid или jwt без короткого exp)
    refresh_token_str = str(uuid.uuid4())
    db_refresh = RefreshToken(
        user_id=user.id,
        token=refresh_token_str,
        expires_at=datetime.utcnow() + timedelta(days=30)
    )
    db.add(db_refresh)
    await db.commit()

    return {
        "access_token": access_token,
        "refresh_token": refresh_token_str,
        "token_type": "bearer"
    }


@router.post("/logout")
async def logout(
    payload: RefreshTokenRequest,
    db: AsyncSession = Depends(get_db)
):
    result = await db.execute(
        select(RefreshToken).where(RefreshToken.token == payload.refresh_token)
    )
    db_token = result.scalars().first()
    if db_token:
        await db.delete(db_token)
        await db.commit()
    return {"message": "Successfully logged out. Refresh token revoked."}


@router.post("/refresh", response_model=TokenResponse)
async def refresh(
    payload: RefreshTokenRequest,
    db: AsyncSession = Depends(get_db)
):
    result = await db.execute(
        select(RefreshToken).where(RefreshToken.token == payload.refresh_token)
    )
    db_token = result.scalars().first()

    if not db_token or db_token.expires_at < datetime.utcnow():
        if db_token:
            await db.delete(db_token)
            await db.commit()
        raise HTTPException(
            status_code=401,
            detail="Invalid or expired refresh token."
        )

    user_id = db_token.user_id
    # Генерируем новые токены (одноразовый refresh-токен для безопасности)
    new_access = create_access_token(data={"sub": str(user_id)})
    new_refresh_str = str(uuid.uuid4())

    # Обновляем токен в БД
    db_token.token = new_refresh_str
    db_token.expires_at = datetime.utcnow() + timedelta(days=30)
    await db.commit()

    return {
        "access_token": new_access,
        "refresh_token": new_refresh_str,
        "token_type": "bearer"
    }
