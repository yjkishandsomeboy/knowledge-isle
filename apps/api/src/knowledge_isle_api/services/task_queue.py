from celery import Celery  # type: ignore[import-untyped]

from knowledge_isle_api.core.config import settings

celery_client = Celery("knowledge_isle_api", broker=settings.redis_url)


def queue_document_processing(document_id: str) -> None:
    celery_client.send_task("documents.process", args=[document_id])
