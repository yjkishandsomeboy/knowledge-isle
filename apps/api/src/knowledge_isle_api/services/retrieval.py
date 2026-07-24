import asyncio
import logging
import re
import time
from dataclasses import dataclass

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from knowledge_isle_api.models.document import Document
from knowledge_isle_api.models.document_chunk import DocumentChunk
from knowledge_isle_api.services.embeddings import embed_texts

logger = logging.getLogger("knowledge_isle.retrieval")


@dataclass(frozen=True)
class RetrievedEvidence:
    document_id: str
    filename: str
    snippet: str
    score: float
    chunk_id: str | None = None
    start_offset: int | None = None
    end_offset: int | None = None


def _terms(question: str) -> set[str]:
    return {term.lower() for term in re.findall(r"[\w\u4e00-\u9fff]+", question) if len(term) > 1}


async def retrieve_evidence(
    session: AsyncSession,
    *,
    knowledge_base_id: str,
    question: str,
    limit: int = 6,
) -> list[RetrievedEvidence]:
    started = time.perf_counter()
    rows = list(await session.execute(
        select(Document, DocumentChunk)
        .outerjoin(DocumentChunk, DocumentChunk.document_id == Document.id)
        .where(
            Document.knowledge_base_id == knowledge_base_id,
            Document.status == "processed",
            Document.extracted_text.is_not(None),
        )
    ))
    documents = [(document, chunk) for document, chunk in rows]
    lexical, filename, semantic = await asyncio.gather(
        asyncio.to_thread(_lexical_search, documents, question),
        asyncio.to_thread(_filename_search, documents, question),
        _semantic_search(session, knowledge_base_id, question),
    )
    merged: dict[str, RetrievedEvidence] = {}
    for item in [*lexical, *filename, *semantic]:
        key = item.chunk_id or item.document_id
        existing = merged.get(key)
        if existing is None or item.score > existing.score:
            merged[key] = item
    evidence = sorted(merged.values(), key=lambda item: item.score, reverse=True)[:limit]
    logger.info(
        "retrieval_complete knowledge_base_id=%s candidates=%d returned=%d duration_ms=%.2f",
        knowledge_base_id,
        len(documents),
        len(evidence),
        (time.perf_counter() - started) * 1000,
    )
    return evidence


async def _semantic_search(
    session: AsyncSession, knowledge_base_id: str, question: str
) -> list[RetrievedEvidence]:
    vectors = await embed_texts([question])
    if not vectors or not vectors[0]:
        return []
    bind = session.bind
    if bind is None or bind.dialect.name != "postgresql":
        return []
    query_vector = vectors[0]
    distance = DocumentChunk.embedding.op("<=>")(query_vector).label("distance")
    rows = await session.execute(
        select(Document, DocumentChunk, distance)
        .join(DocumentChunk, DocumentChunk.document_id == Document.id)
        .where(
            Document.knowledge_base_id == knowledge_base_id,
            Document.status == "processed",
            DocumentChunk.embedding.is_not(None),
        )
        .order_by(distance)
        .limit(12)
    )
    return [
        RetrievedEvidence(
            document.id,
            document.original_filename,
            chunk.content[:900].strip(),
            max(0.0, 1.0 - float(distance_value)) * 10,
            chunk.id,
            chunk.start_offset,
            chunk.end_offset,
        )
        for document, chunk, distance_value in rows
    ]


def _lexical_search(
    documents: list[tuple[Document, DocumentChunk | None]], question: str
) -> list[RetrievedEvidence]:
    terms = _terms(question)
    results: list[RetrievedEvidence] = []
    for document, chunk in documents:
        text = chunk.content if chunk is not None else (document.extracted_text or "")
        lowered = text.lower()
        score = float(sum(lowered.count(term) for term in terms))
        if score <= 0:
            continue
        first_position = min((lowered.find(term) for term in terms if term in lowered), default=0)
        start = max(0, first_position - 180)
        snippet = text[start : start + 900].strip()
        results.append(
            RetrievedEvidence(
                document.id, document.original_filename, snippet, score,
                chunk.id if chunk else None,
                (chunk.start_offset + start) if chunk else None,
                (chunk.start_offset + start + len(snippet)) if chunk else None,
            )
        )
    return results


def _filename_search(
    documents: list[tuple[Document, DocumentChunk | None]], question: str
) -> list[RetrievedEvidence]:
    terms = _terms(question)
    results: list[RetrievedEvidence] = []
    for document, chunk in documents:
        filename = document.original_filename.lower()
        score = float(sum(3 for term in terms if term in filename))
        if score > 0:
            results.append(
                RetrievedEvidence(
                    document.id,
                    document.original_filename,
                    (chunk.content if chunk else (document.extracted_text or ""))[:900].strip(),
                    score,
                    chunk.id if chunk else None,
                    chunk.start_offset if chunk else None,
                    chunk.end_offset if chunk else None,
                )
            )
    return results
