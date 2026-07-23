from fastapi.testclient import TestClient

from knowledge_isle_api.main import app


def test_health_check() -> None:
    response = TestClient(app).get("/api/v1/health")

    assert response.status_code == 200
    assert response.json() == {
        "status": "ok",
        "service": "knowledge-isle-api",
        "version": "0.1.0",
    }
