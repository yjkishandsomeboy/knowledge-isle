from typing import Annotated

from fastapi import Cookie, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from knowledge_isle_api.core.config import settings
from knowledge_isle_api.db.session import get_db_session
from knowledge_isle_api.models.user import User
from knowledge_isle_api.services.auth import get_user_for_token

DatabaseSession = Annotated[AsyncSession, Depends(get_db_session)]
SessionCookie = Annotated[str | None, Cookie(alias=settings.session_cookie_name)]


async def get_optional_user(session: DatabaseSession, token: SessionCookie = None) -> User | None:
    if token is None:
        return None
    return await get_user_for_token(session, token)


async def require_user(user: Annotated[User | None, Depends(get_optional_user)]) -> User:
    if user is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Not authenticated")
    return user


CurrentUser = Annotated[User, Depends(require_user)]
