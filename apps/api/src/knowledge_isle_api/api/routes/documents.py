from fastapi import APIRouter, HTTPException, UploadFile, status

from knowledge_isle_api.api.dependencies import CurrentUser, DatabaseSession
from knowledge_isle_api.schemas.document import DocumentResponse
from knowledge_isle_api.services.documents import (
    ALLOWED_CONTENT_TYPES,
    create_document,
    list_documents,
)
from knowledge_isle_api.services.knowledge_bases import get_knowledge_base

router = APIRouter(prefix="/knowledge-bases/{knowledge_base_id}/documents", tags=["documents"])


@router.get("", response_model=list[DocumentResponse])
async def list_documents_route(
    knowledge_base_id: str,
    session: DatabaseSession,
    user: CurrentUser,
) -> list[DocumentResponse]:
    knowledge_base = await get_knowledge_base(
        session, knowledge_base_id=knowledge_base_id, owner_id=user.id
    )
    if knowledge_base is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Knowledge base not found"
        )
    documents = await list_documents(session, knowledge_base_id)
    return [DocumentResponse.model_validate(item) for item in documents]


@router.post("", response_model=DocumentResponse, status_code=status.HTTP_201_CREATED)
async def upload_document_route(
    knowledge_base_id: str,
    file: UploadFile,
    session: DatabaseSession,
    user: CurrentUser,
) -> DocumentResponse:
    knowledge_base = await get_knowledge_base(
        session, knowledge_base_id=knowledge_base_id, owner_id=user.id
    )
    if knowledge_base is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Knowledge base not found"
        )
    content_type = file.content_type or "application/octet-stream"
    if content_type not in ALLOWED_CONTENT_TYPES:
        raise HTTPException(
            status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
            detail="Only PDF, Markdown, and TXT files are supported",
        )
    content = await file.read()
    if not content:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="File is empty"
        )
    document = await create_document(
        session,
        knowledge_base_id=knowledge_base_id,
        filename=file.filename or "untitled",
        content_type=content_type,
        content=content,
    )
    return DocumentResponse.model_validate(document)
