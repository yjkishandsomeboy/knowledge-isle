import secrets
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Response, status

from knowledge_isle_api.api.dependencies import (
    CurrentUser,
    DatabaseSession,
    SessionCookie,
    get_optional_user,
)
from knowledge_isle_api.core.config import settings
from knowledge_isle_api.models.user import User
from knowledge_isle_api.schemas.auth import (
    AuthStatusResponse,
    LoginRequest,
    SetupRequest,
    UserResponse,
)
from knowledge_isle_api.services.auth import (
    AlreadyInitializedError,
    authenticate,
    create_admin,
    create_user_session,
    is_initialized,
    revoke_session,
)

router = APIRouter(prefix="/auth", tags=["authentication"])


def set_session_cookie(response: Response, token: str) -> None:
    response.set_cookie(
        key=settings.session_cookie_name,
        value=token,
        max_age=settings.session_ttl_days * 24 * 60 * 60,
        httponly=True,
        secure=settings.app_env == "production",
        samesite="strict",
        path="/",
    )


@router.get("/status", response_model=AuthStatusResponse)
async def auth_status(
    session: DatabaseSession,
    user: Annotated[User | None, Depends(get_optional_user)],
) -> AuthStatusResponse:
    user_response = UserResponse.model_validate(user) if user is not None else None
    return AuthStatusResponse(
        initialized=await is_initialized(session),
        authenticated=user is not None,
        user=user_response,
    )


@router.post("/setup", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def setup_admin(
    payload: SetupRequest,
    response: Response,
    session: DatabaseSession,
) -> UserResponse:
    if not secrets.compare_digest(payload.setup_token, settings.admin_setup_token):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Invalid setup token")
    try:
        user = await create_admin(
            session,
            email=str(payload.email),
            password=payload.password,
            locale=payload.locale,
        )
    except AlreadyInitializedError as error:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Already initialized",
        ) from error

    set_session_cookie(response, await create_user_session(session, user))
    return UserResponse.model_validate(user)


@router.post("/login", response_model=UserResponse)
async def login(
    payload: LoginRequest,
    response: Response,
    session: DatabaseSession,
) -> UserResponse:
    user = await authenticate(session, email=str(payload.email), password=payload.password)
    if user is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")
    set_session_cookie(response, await create_user_session(session, user))
    return UserResponse.model_validate(user)


@router.get("/me", response_model=UserResponse)
async def current_user(user: CurrentUser) -> UserResponse:
    return UserResponse.model_validate(user)


@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT)
async def logout(
    response: Response,
    session: DatabaseSession,
    token: SessionCookie = None,
) -> None:
    if token is not None:
        await revoke_session(session, token)
    response.delete_cookie(
        settings.session_cookie_name,
        path="/",
        secure=settings.app_env == "production",
        httponly=True,
        samesite="strict",
    )
