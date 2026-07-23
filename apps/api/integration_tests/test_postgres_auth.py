import os

import pytest
from fastapi.testclient import TestClient

if "INTEGRATION_DATABASE_URL" not in os.environ:
    pytest.skip("INTEGRATION_DATABASE_URL is required", allow_module_level=True)

os.environ["DATABASE_URL"] = os.environ["INTEGRATION_DATABASE_URL"]
os.environ["ADMIN_SETUP_TOKEN"] = "postgres-integration-setup-token"

from knowledge_isle_api.main import app  # noqa: E402


def test_authentication_round_trip_on_postgres() -> None:
    with TestClient(app) as client:
        setup_response = client.post(
            "/api/v1/auth/setup",
            json={
                "email": "postgres-test@example.com",
                "password": "integration-password-2026",
                "setupToken": "postgres-integration-setup-token",
                "locale": "zh-CN",
            },
        )
        assert setup_response.status_code == 201
        assert "HttpOnly" in setup_response.headers["set-cookie"]

        client.cookies.clear()
        login_response = client.post(
            "/api/v1/auth/login",
            json={
                "email": "postgres-test@example.com",
                "password": "integration-password-2026",
            },
        )
        assert login_response.status_code == 200
        assert client.get("/api/v1/dashboard").status_code == 200

        assert client.post("/api/v1/auth/logout").status_code == 204
        assert client.get("/api/v1/dashboard").status_code == 401
