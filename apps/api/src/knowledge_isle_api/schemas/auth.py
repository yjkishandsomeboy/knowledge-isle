from datetime import datetime
from typing import Literal

from pydantic import EmailStr, Field

from knowledge_isle_api.schemas.base import ApiSchema

Locale = Literal["zh-CN", "en-US"]


class SetupRequest(ApiSchema):
    email: EmailStr
    password: str = Field(min_length=12, max_length=128)
    setup_token: str = Field(min_length=1, max_length=512)
    locale: Locale = "zh-CN"


class LoginRequest(ApiSchema):
    email: EmailStr
    password: str = Field(min_length=1, max_length=128)


class UserResponse(ApiSchema):
    id: str
    email: EmailStr
    locale: Locale
    created_at: datetime


class AuthStatusResponse(ApiSchema):
    initialized: bool
    authenticated: bool
    user: UserResponse | None
