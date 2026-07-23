from fastapi.testclient import TestClient
from test_auth import setup_admin


def test_knowledge_bases_require_authentication(client: TestClient) -> None:
    response = client.get("/api/v1/knowledge-bases")

    assert response.status_code == 401


def test_knowledge_base_crud(client: TestClient) -> None:
    setup_admin(client)

    create_response = client.post(
        "/api/v1/knowledge-bases",
        json={
            "name": "  Product Notes  ",
            "description": "Useful internal notes",
            "defaultLocale": "en-US",
        },
    )
    assert create_response.status_code == 201
    knowledge_base = create_response.json()
    assert knowledge_base["name"] == "Product Notes"
    assert knowledge_base["defaultLocale"] == "en-US"

    list_response = client.get("/api/v1/knowledge-bases")
    assert list_response.status_code == 200
    assert [item["id"] for item in list_response.json()] == [knowledge_base["id"]]

    update_response = client.patch(
        f"/api/v1/knowledge-bases/{knowledge_base['id']}",
        json={"name": "Product Handbook", "description": "Updated notes"},
    )
    assert update_response.status_code == 200
    assert update_response.json()["name"] == "Product Handbook"

    delete_response = client.delete(f"/api/v1/knowledge-bases/{knowledge_base['id']}")
    assert delete_response.status_code == 204
    assert client.get("/api/v1/knowledge-bases").json() == []


def test_knowledge_base_rejects_blank_name(client: TestClient) -> None:
    setup_admin(client)

    response = client.post("/api/v1/knowledge-bases", json={"name": "   "})

    assert response.status_code == 422
