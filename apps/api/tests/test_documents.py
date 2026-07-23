from fastapi.testclient import TestClient
from test_auth import setup_admin

from knowledge_isle_api.services import documents as documents_service


def test_document_upload_and_list(client: TestClient, monkeypatch) -> None:
    setup_admin(client)
    knowledge_base = client.post("/api/v1/knowledge-bases", json={"name": "Notes"}).json()

    monkeypatch.setattr(documents_service.storage, "put", lambda *_args: None)
    monkeypatch.setattr(documents_service, "queue_document_processing", lambda *_args: None)
    response = client.post(
        f"/api/v1/knowledge-bases/{knowledge_base['id']}/documents",
        files={"file": ("readme.md", b"# Hello\n\nKnowledge Isle", "text/markdown")},
    )

    assert response.status_code == 201
    document = response.json()
    assert document["originalFilename"] == "readme.md"
    assert document["status"] == "processing"
    assert document["extractedText"] is None

    list_response = client.get(
        f"/api/v1/knowledge-bases/{knowledge_base['id']}/documents"
    )
    assert list_response.status_code == 200
    assert list_response.json()[0]["id"] == document["id"]


def test_document_upload_rejects_unsupported_type(client: TestClient) -> None:
    setup_admin(client)
    knowledge_base = client.post("/api/v1/knowledge-bases", json={"name": "Notes"}).json()

    response = client.post(
        f"/api/v1/knowledge-bases/{knowledge_base['id']}/documents",
        files={"file": ("image.png", b"not an image", "image/png")},
    )

    assert response.status_code == 415
