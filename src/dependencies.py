from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from database import get_db
from models import User, UserGroup, UserGroupEnum
from security import decode_token

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="auth/login")

async def get_current_user(
    token: str = Depends(oauth2_scheme), 
    db: AsyncSession = Depends(get_db)
) -> User:
    payload = decode_token(token)
    user_id_str = payload.get("sub")
    if not user_id_str:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token invalid: missing user identifier."
        )
    
    result = await db.execute(
        select(User).where(User.id == int(user_id_str))
    )
    user = result.scalars().first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found."
        )
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User account is inactive."
        )
    return user


class RoleChecker:
    def __init__(self, allowed_roles: list[UserGroupEnum]):
        self.allowed_roles = allowed_roles

    async def __call__(
        self, 
        current_user: User = Depends(get_current_user), 
        db: AsyncSession = Depends(get_db)
    ) -> User:
        # Загружаем имя группы пользователя
        result = await db.execute(
            select(UserGroup).where(UserGroup.id == current_user.group_id)
        )
        group = result.scalars().first()
        
        if not group or group.name not in self.allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You do not have enough permissions to perform this action."
            )
        return current_user

# Быстрые алиасы для ролей
allow_moderator_or_admin = RoleChecker([UserGroupEnum.MODERATOR, UserGroupEnum.ADMIN])
allow_admin_only = RoleChecker([UserGroupEnum.ADMIN])