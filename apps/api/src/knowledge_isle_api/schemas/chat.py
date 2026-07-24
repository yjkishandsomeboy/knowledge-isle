from datetime import datetime

from pydantic import Field

from knowledge_isle_api.schemas.base import ApiSchema


class AskRequest(ApiSchema):
    question: str = Field(min_length=1, max_length=4000)
    conversation_id: str | None = None


class CitationResponse(ApiSchema):
    document_id: str
    filename: str
    snippet: str
    rank: int
    chunk_id: str | None = None
    start_offset: int | None = None
    end_offset: int | None = None


class AskResponse(ApiSchema):
    conversation_id: str
    message_id: str
    answer: str
    citations: list[CitationResponse]
    created_at: datetime
