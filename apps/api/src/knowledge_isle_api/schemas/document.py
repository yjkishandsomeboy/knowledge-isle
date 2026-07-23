from datetime import datetime

from knowledge_isle_api.schemas.base import ApiSchema


class DocumentResponse(ApiSchema):
    id: str
    knowledge_base_id: str
    original_filename: str
    content_type: str
    size_bytes: int
    status: str
    extracted_text: str | None
    error_message: str | None
    created_at: datetime
    updated_at: datetime
