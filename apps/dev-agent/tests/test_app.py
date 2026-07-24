from fastapi.testclient import TestClient

from knowledge_isle_dev_agent.app import app


def test_dashboard_is_bound_to_local_application() -> None:
    response = TestClient(app).get("/")
    assert response.status_code == 200
    assert "Knowledge Isle" in response.text
    assert "Build" in response.text
