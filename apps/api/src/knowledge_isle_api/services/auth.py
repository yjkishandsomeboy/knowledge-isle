from datetime import UTC, datetime, timedelta

from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from knowledge_isle_api.core.config import settings
from knowledge_isle_api.core.security import (
    create_session_token,
    hash_password,
    hash_session_token,
    verify_password,
)
from knowledge_isle_api.models.session import UserSession
from knowledge_isle_api.models.user import User


class AlreadyInitializedError(Exception):
    pass


async def is_initialized(session: AsyncSession) -> bool:
    count = await session.scalar(select(func.count()).select_from(User))
    return bool(count)


async def create_admin(
    session: AsyncSession,
    *,
    email: str,
    password: str,
    locale: str,
) -> User:
    if await is_initialized(session):
        raise AlreadyInitializedError

    user = User(
        singleton_key="admin",
        email=email.lower(),
        password_hash=hash_password(password),
        locale=locale,
    )
    session.add(user)
    try:
        await session.commit()
    except IntegrityError as error:
        await session.rollback()
        raise AlreadyInitializedError from error
    await session.refresh(user)
    return user


async def authenticate(session: AsyncSession, *, email: str, password: str) -> User | None:
    user = await session.scalar(select(User).where(User.email == email.lower()))
    if user is None or not verify_password(user.password_hash, password):
        return None
    return user


async def create_user_session(session: AsyncSession, user: User) -> str:
    token = create_session_token()
    user_session = UserSession(
        user_id=user.id,
        token_hash=hash_session_token(token),
        expires_at=datetime.now(UTC) + timedelta(days=settings.session_ttl_days),
    )
    session.add(user_session)
    await session.commit()
    return token


async def get_user_for_token(session: AsyncSession, token: str) -> User | None:
    user_session = await session.scalar(
        select(UserSession).where(UserSession.token_hash == hash_session_token(token))
    )
    if user_session is None or user_session.revoked_at is not None:
        return None

    expires_at = user_session.expires_at
    if expires_at.tzinfo is None:
        expires_at = expires_at.replace(tzinfo=UTC)
    if expires_at <= datetime.now(UTC):
        return None

    return await session.get(User, user_session.user_id)


async def revoke_session(session: AsyncSession, token: str) -> None:
    user_session = await session.scalar(
        select(UserSession).where(UserSession.token_hash == hash_session_token(token))
    )
    if user_session is None:
        return
    user_session.revoked_at = datetime.now(UTC)
    await session.commit()
