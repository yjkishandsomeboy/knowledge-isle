import asyncio
import importlib
import sys
from collections.abc import Callable, Generator
from types import ModuleType, SimpleNamespace
from typing import Any

import pytest


class FakeColumn:
    def __init__(self, name: str) -> None:
        self.name = name

    def __eq__(self, value: object) -> tuple[str, str, object]:
        return ("eq", self.name, value)


class FakeStatement:
    def __init__(self, operation: str, model: type[object]) -> None:
        self.operation = operation
        self.model = model
        self.criterion: object | None = None

    def where(self, criterion: object) -> "FakeStatement":
        self.criterion = criterion
        return self


class FakeDocument:
    id = FakeColumn("document.id")


class FakeDocumentChunk:
    document_id = FakeColumn("document_chunk.document_id")

    def __init__(self, **values: object) -> None:
        self.__dict__.update(values)


class FakeSession:
    def __init__(self, document: object | None) -> None:
        self.document = document
        self.statements: list[FakeStatement] = []
        self.added: list[FakeDocumentChunk] = []
        self.operations: list[str] = []
        self.commit_count = 0

    async def __aenter__(self) -> "FakeSession":
        return self

    async def __aexit__(self, *args: object) -> None:
        return None

    async def scalar(self, statement: FakeStatement) -> object | None:
        self.operations.append("scalar")
        self.statements.append(statement)
        return self.document

    async def execute(self, statement: FakeStatement) -> None:
        self.operations.append("execute")
        self.statements.append(statement)

    def add_all(self, chunks: Generator[FakeDocumentChunk, None, None]) -> None:
        self.operations.append("add_all")
        self.added.extend(chunks)

    async def commit(self) -> None:
        self.operations.append("commit")
        self.commit_count += 1


class FakeCeleryApp:
    def task(self, **_options: object) -> Callable[[Callable[..., Any]], Callable[..., Any]]:
        return lambda function: function


class RetryRequested(Exception):
    pass


class FakeTask:
    def __init__(self, retries: int, max_retries: int = 2) -> None:
        self.request = SimpleNamespace(retries=retries)
        self.max_retries = max_retries
        self.retry_call: tuple[Exception, int] | None = None

    def retry(self, *, exc: Exception, countdown: int) -> None:
        self.retry_call = (exc, countdown)
        raise RetryRequested


def make_module(name: str, **attributes: object) -> ModuleType:
    module = ModuleType(name)
    module.__dict__.update(attributes)
    return module


@pytest.fixture
def tasks_module(monkeypatch: pytest.MonkeyPatch) -> Generator[ModuleType, None, None]:
    async def unused_embed_texts(_texts: list[str]) -> None:
        raise AssertionError("embed_texts should be replaced by the test")

    def unused_dependency(*_args: object, **_kwargs: object) -> None:
        raise AssertionError("dependency should be replaced by the test")

    modules = {
        "knowledge_isle_api": make_module("knowledge_isle_api", __path__=[]),
        "knowledge_isle_api.db": make_module("knowledge_isle_api.db", __path__=[]),
        "knowledge_isle_api.db.session": make_module(
            "knowledge_isle_api.db.session", session_factory=unused_dependency
        ),
        "knowledge_isle_api.models": make_module("knowledge_isle_api.models", __path__=[]),
        "knowledge_isle_api.models.document": make_module(
            "knowledge_isle_api.models.document", Document=FakeDocument
        ),
        "knowledge_isle_api.models.document_chunk": make_module(
            "knowledge_isle_api.models.document_chunk", DocumentChunk=FakeDocumentChunk
        ),
        "knowledge_isle_api.services": make_module("knowledge_isle_api.services", __path__=[]),
        "knowledge_isle_api.services.chunking": make_module(
            "knowledge_isle_api.services.chunking", split_text=unused_dependency
        ),
        "knowledge_isle_api.services.documents": make_module(
            "knowledge_isle_api.services.documents",
            ALLOWED_CONTENT_TYPES={"text/markdown": "md"},
            extract_text=unused_dependency,
        ),
        "knowledge_isle_api.services.embeddings": make_module(
            "knowledge_isle_api.services.embeddings", embed_texts=unused_embed_texts
        ),
        "knowledge_isle_api.services.storage": make_module(
            "knowledge_isle_api.services.storage",
            storage=SimpleNamespace(get=unused_dependency),
        ),
        "knowledge_isle_worker.celery_app": make_module(
            "knowledge_isle_worker.celery_app", celery_app=FakeCeleryApp()
        ),
    }
    for name, module in modules.items():
        monkeypatch.setitem(sys.modules, name, module)
    monkeypatch.delitem(sys.modules, "knowledge_isle_worker.tasks", raising=False)

    tasks = importlib.import_module("knowledge_isle_worker.tasks")
    monkeypatch.setattr(tasks, "select", lambda model: FakeStatement("select", model))
    monkeypatch.setattr(tasks, "delete", lambda model: FakeStatement("delete", model))
    try:
        yield tasks
    finally:
        sys.modules.pop("knowledge_isle_worker.tasks", None)


def test_missing_document_returns_missing(
    tasks_module: ModuleType, monkeypatch: pytest.MonkeyPatch
) -> None:
    session = FakeSession(document=None)
    monkeypatch.setattr(tasks_module, "session_factory", lambda: session)

    result = asyncio.run(tasks_module._process_document("missing-document"))

    assert result == "missing"
    assert session.operations == ["scalar"]
    assert session.statements[0].criterion == ("eq", "document.id", "missing-document")


def test_successful_processing_replaces_chunks_and_updates_document(
    tasks_module: ModuleType, monkeypatch: pytest.MonkeyPatch
) -> None:
    document = SimpleNamespace(
        id="document-1",
        object_key="documents/document-1.md",
        content_type="text/markdown",
        extracted_text=None,
        status="processing",
        error_message="old error",
    )
    session = FakeSession(document=document)
    storage_calls: list[str] = []
    extraction_calls: list[tuple[bytes, str]] = []
    split_calls: list[str] = []
    embedding_calls: list[list[str]] = []
    chunks = [
        SimpleNamespace(index=0, content="First chunk", start_offset=0, end_offset=11),
        SimpleNamespace(index=1, content="Second", start_offset=12, end_offset=18),
    ]
    embeddings = [[0.1, 0.2], [0.3, 0.4]]

    def get_object(object_key: str) -> bytes:
        storage_calls.append(object_key)
        return b"raw document"

    def extract_text(content: bytes, extension: str) -> str:
        extraction_calls.append((content, extension))
        return "First chunk Second"

    def split_text(text: str) -> list[SimpleNamespace]:
        split_calls.append(text)
        return chunks

    async def embed_texts(texts: list[str]) -> list[list[float]]:
        embedding_calls.append(texts)
        return embeddings

    monkeypatch.setattr(tasks_module, "session_factory", lambda: session)
    monkeypatch.setattr(tasks_module.storage, "get", get_object)
    monkeypatch.setattr(tasks_module, "extract_text", extract_text)
    monkeypatch.setattr(tasks_module, "split_text", split_text)
    monkeypatch.setattr(tasks_module, "embed_texts", embed_texts)

    result = asyncio.run(tasks_module._process_document(document.id))

    assert result == "processed"
    assert storage_calls == [document.object_key]
    assert extraction_calls == [(b"raw document", "md")]
    assert split_calls == ["First chunk Second"]
    assert embedding_calls == [["First chunk", "Second"]]
    assert session.operations == ["scalar", "execute", "add_all", "commit"]
    assert session.statements[1].operation == "delete"
    assert session.statements[1].criterion == (
        "eq",
        "document_chunk.document_id",
        document.id,
    )
    assert [
        (
            chunk.chunk_index,
            chunk.content,
            chunk.start_offset,
            chunk.end_offset,
            chunk.char_count,
            chunk.embedding,
        )
        for chunk in session.added
    ] == [
        (0, "First chunk", 0, 11, 11, embeddings[0]),
        (1, "Second", 12, 18, 6, embeddings[1]),
    ]
    assert document.extracted_text == "First chunk Second"
    assert document.status == "processed"
    assert document.error_message is None
    assert session.commit_count == 1


def test_non_terminal_failure_requests_retry(
    tasks_module: ModuleType, monkeypatch: pytest.MonkeyPatch
) -> None:
    error = RuntimeError("temporary failure")
    task = FakeTask(retries=1)

    async def fail_processing(_document_id: str) -> str:
        raise error

    async def fail_if_marked(_document_id: str, _error_message: str) -> None:
        raise AssertionError("non-terminal failures must not be marked failed")

    monkeypatch.setattr(tasks_module, "_process_document", fail_processing)
    monkeypatch.setattr(tasks_module, "_mark_failed", fail_if_marked)

    with pytest.raises(RetryRequested):
        tasks_module.process_document(task, "document-1")

    assert task.retry_call == (error, 10)


def test_terminal_failure_marks_document_failed_and_truncates_error(
    tasks_module: ModuleType, monkeypatch: pytest.MonkeyPatch
) -> None:
    long_message = "failure-" + ("x" * 1100)
    error = RuntimeError(long_message)
    document = SimpleNamespace(status="processing", error_message=None)
    session = FakeSession(document=document)
    task = FakeTask(retries=2)

    async def fail_processing(_document_id: str) -> str:
        raise error

    monkeypatch.setattr(tasks_module, "_process_document", fail_processing)
    monkeypatch.setattr(tasks_module, "session_factory", lambda: session)

    with pytest.raises(RuntimeError, match="failure-") as raised:
        tasks_module.process_document(task, "document-1")

    assert raised.value is error
    assert task.retry_call is None
    assert session.operations == ["scalar", "commit"]
    assert document.status == "failed"
    assert document.error_message == long_message[:1000]
    assert session.commit_count == 1
