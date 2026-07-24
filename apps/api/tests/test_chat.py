from fastapi.testclient import TestClient
from sqlalchemy import select
from test_auth import setup_admin

from knowledge_isle_api.models.document import Document
from knowledge_isle_api.models.document_chunk import DocumentChunk
from knowledge_isle_api.services import ai_provider


def test_chat_retrieves_evidence_and_saves_citations(
    client: TestClient, monkeypatch
) -> None:
    setup_admin(client)
    knowledge_base = client.post("/api/v1/knowledge-bases", json={"name": "Product"}).json()

    async def seed_document() -> None:
        from knowledge_isle_api.db.session import get_db_session
        from knowledge_isle_api.main import app

        override = app.dependency_overrides[get_db_session]
        async for session in override():
            document = Document(
                    knowledge_base_id=knowledge_base["id"],
                    original_filename="handbook.md",
                    object_key="test/handbook.md",
                    content_type="text/markdown",
                    size_bytes=100,
                    status="processed",
                    extracted_text=(
                        "Knowledge Isle supports private documents and traceable citations."
                    ),
                )
            session.add(document)
            await session.flush()
            session.add(
                DocumentChunk(
                    document_id=document.id,
                    chunk_index=0,
                    content="Knowledge Isle supports private documents and traceable citations.",
                    start_offset=0,
                    end_offset=65,
                    char_count=65,
                )
            )
            await session.commit()
            assert await session.scalar(select(Document.id)) is not None

    import asyncio

    asyncio.run(seed_document())

    async def fake_answer(_question, evidence) -> str:
        assert evidence
        return "The platform supports private documents [1]."

    monkeypatch.setattr(ai_provider, "generate_answer", fake_answer)
    monkeypatch.setattr("knowledge_isle_api.services.chat.generate_answer", fake_answer)

    response = client.post(
        f"/api/v1/knowledge-bases/{knowledge_base['id']}/chat",
        json={"question": "What private documents does Knowledge Isle support?"},
    )

    assert response.status_code == 200
    body = response.json()
    assert body["answer"] == "The platform supports private documents [1]."
    assert body["citations"][0]["filename"] == "handbook.md"
    assert body["citations"][0]["chunkId"]
    assert body["conversationId"]


def test_chat_requires_authentication(client: TestClient) -> None:
    response = client.post(
        "/api/v1/knowledge-bases/missing/chat", json={"question": "Hello"}
    )

    assert response.status_code == 401


def test_stream_chat_returns_deltas_and_done_event(client: TestClient, monkeypatch) -> None:
    setup_admin(client)
    knowledge_base = client.post("/api/v1/knowledge-bases", json={"name": "Stream"}).json()

    async def fake_stream(_question, _evidence):
        yield "第一段"
        yield "第二段"

    monkeypatch.setattr("knowledge_isle_api.services.chat.stream_answer", fake_stream)
    response = client.post(
        f"/api/v1/knowledge-bases/{knowledge_base['id']}/chat/stream",
        json={"question": "流式测试"},
    )

    assert response.status_code == 200
    assert "event: delta" in response.text
    assert '"text": "第一段"' in response.text
    assert "event: done" in response.text
