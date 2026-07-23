from io import BytesIO
from uuid import uuid4

from pypdf import PdfReader
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from knowledge_isle_api.models.document import Document
from knowledge_isle_api.services.storage import storage
from knowledge_isle_api.services.task_queue import queue_document_processing

ALLOWED_CONTENT_TYPES = {
    "text/plain": "txt",
    "text/markdown": "md",
    "text/x-markdown": "md",
    "application/pdf": "pdf",
}


def extract_text(content: bytes, extension: str) -> str:
    if extension == "pdf":
        reader = PdfReader(BytesIO(content))
        return "\n\n".join(page.extract_text() or "" for page in reader.pages).strip()
    return content.decode("utf-8-sig").strip()


async def list_documents(session: AsyncSession, knowledge_base_id: str) -> list[Document]:
    result = await session.scalars(
        select(Document)
        .where(Document.knowledge_base_id == knowledge_base_id)
        .order_by(Document.created_at.desc())
    )
    return list(result)


async def create_document(
    session: AsyncSession,
    *,
    knowledge_base_id: str,
    filename: str,
    content_type: str,
    content: bytes,
) -> Document:
    extension = ALLOWED_CONTENT_TYPES[content_type]
    document_id = str(uuid4())
    object_key = f"knowledge-bases/{knowledge_base_id}/documents/{document_id}.{extension}"
    document = Document(
        id=document_id,
        knowledge_base_id=knowledge_base_id,
        original_filename=filename,
        object_key=object_key,
        content_type=content_type,
        size_bytes=len(content),
        status="processing",
    )
    session.add(document)
    try:
        storage.put(object_key, content, content_type)
    except Exception as error:
        document.status = "failed"
        document.error_message = str(error)[:1000]
    await session.commit()
    await session.refresh(document)
    if document.status == "processing":
        try:
            queue_document_processing(document.id)
        except Exception as error:
            document.status = "failed"
            document.error_message = f"Unable to queue processing: {error}"[:1000]
            await session.commit()
            await session.refresh(document)
    return document
