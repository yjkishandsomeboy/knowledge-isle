import asyncio
import re
from dataclasses import dataclass

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from knowledge_isle_api.models.document import Document
from knowledge_isle_api.models.document_chunk import DocumentChunk


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
    lexical, filename = await asyncio.gather(
        asyncio.to_thread(_lexical_search, documents, question),
        asyncio.to_thread(_filename_search, documents, question),
    )
    merged: dict[str, RetrievedEvidence] = {}
    for item in [*lexical, *filename]:
        key = item.chunk_id or item.document_id
        existing = merged.get(key)
        if existing is None or item.score > existing.score:
            merged[key] = item
    return sorted(merged.values(), key=lambda item: item.score, reverse=True)[:limit]


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
