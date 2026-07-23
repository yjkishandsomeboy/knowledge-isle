from datetime import datetime
from typing import Literal

from pydantic import Field, field_validator

from knowledge_isle_api.schemas.base import ApiSchema

Locale = Literal["zh-CN", "en-US"]


class KnowledgeBaseCreate(ApiSchema):
    name: str = Field(min_length=1, max_length=120)
    description: str | None = Field(default=None, max_length=2000)
    default_locale: Locale = "zh-CN"

    @field_validator("name")
    @classmethod
    def validate_name(cls, value: str) -> str:
        cleaned = value.strip()
        if not cleaned:
            raise ValueError("Name cannot be blank")
        return cleaned


class KnowledgeBaseUpdate(ApiSchema):
    name: str | None = Field(default=None, min_length=1, max_length=120)
    description: str | None = Field(default=None, max_length=2000)
    default_locale: Locale | None = None

    @field_validator("name")
    @classmethod
    def validate_name(cls, value: str | None) -> str | None:
        if value is None:
            return None
        cleaned = value.strip()
        if not cleaned:
            raise ValueError("Name cannot be blank")
        return cleaned


class KnowledgeBaseResponse(ApiSchema):
    id: str
    name: str
    description: str | None
    default_locale: Locale
    created_at: datetime
    updated_at: datetime
