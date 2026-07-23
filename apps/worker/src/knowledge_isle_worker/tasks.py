import asyncio

from knowledge_isle_api.db.session import session_factory
from knowledge_isle_api.models.document import Document
from knowledge_isle_api.services.documents import ALLOWED_CONTENT_TYPES, extract_text
from knowledge_isle_api.services.storage import storage
from sqlalchemy import select

from knowledge_isle_worker.celery_app import celery_app


@celery_app.task(name="documents.process", bind=True, max_retries=2)
def process_document(self, document_id: str) -> str:
    try:
        return asyncio.run(_process_document(document_id))
    except Exception as error:
        if self.request.retries >= self.max_retries:
            asyncio.run(_mark_failed(document_id, str(error)))
            raise
        raise self.retry(exc=error, countdown=10) from error


async def _process_document(document_id: str) -> str:
    async with session_factory() as session:
        document = await session.scalar(select(Document).where(Document.id == document_id))
        if document is None:
            return "missing"
        extension = ALLOWED_CONTENT_TYPES.get(document.content_type)
        if extension is None:
            await _mark_failed(document_id, "Unsupported content type")
            return "failed"
        content = storage.get(document.object_key)
        document.extracted_text = extract_text(content, extension)
        document.status = "processed"
        document.error_message = None
        await session.commit()
        return "processed"


async def _mark_failed(document_id: str, error_message: str) -> None:
    async with session_factory() as session:
        document = await session.scalar(select(Document).where(Document.id == document_id))
        if document is not None:
            document.status = "failed"
            document.error_message = error_message[:1000]
            await session.commit()
