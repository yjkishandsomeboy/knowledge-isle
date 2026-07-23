from fastapi.testclient import TestClient


def setup_admin(client: TestClient) -> dict[str, object]:
    response = client.post(
        "/api/v1/auth/setup",
        json={
            "email": "admin@example.com",
            "password": "correct-horse-battery-staple",
            "setupToken": "test-setup-token",
            "locale": "zh-CN",
        },
    )
    assert response.status_code == 201
    return response.json()


def test_setup_status_starts_uninitialized(client: TestClient) -> None:
    response = client.get("/api/v1/auth/status")

    assert response.status_code == 200
    assert response.json() == {"initialized": False, "authenticated": False, "user": None}


def test_admin_can_only_be_initialized_once(client: TestClient) -> None:
    user = setup_admin(client)

    assert user["email"] == "admin@example.com"
    assert user["locale"] == "zh-CN"
    assert client.get("/api/v1/auth/status").json()["authenticated"] is True

    second_response = client.post(
        "/api/v1/auth/setup",
        json={
            "email": "other@example.com",
            "password": "another-secure-password",
            "setupToken": "test-setup-token",
            "locale": "en-US",
        },
    )

    assert second_response.status_code == 409


def test_setup_rejects_invalid_token(client: TestClient) -> None:
    response = client.post(
        "/api/v1/auth/setup",
        json={
            "email": "admin@example.com",
            "password": "correct-horse-battery-staple",
            "setupToken": "wrong-token",
            "locale": "zh-CN",
        },
    )

    assert response.status_code == 403


def test_login_creates_session_and_logout_revokes_it(client: TestClient) -> None:
    setup_admin(client)
    client.cookies.clear()

    login_response = client.post(
        "/api/v1/auth/login",
        json={"email": "admin@example.com", "password": "correct-horse-battery-staple"},
    )

    assert login_response.status_code == 200
    assert "knowledge_isle_session" in client.cookies
    assert "HttpOnly" in login_response.headers["set-cookie"]
    assert client.get("/api/v1/auth/me").status_code == 200
    assert client.get("/api/v1/dashboard").status_code == 200

    logout_response = client.post("/api/v1/auth/logout")

    assert logout_response.status_code == 204
    assert client.get("/api/v1/auth/me").status_code == 401
    assert client.get("/api/v1/dashboard").status_code == 401


def test_login_rejects_wrong_password(client: TestClient) -> None:
    setup_admin(client)
    client.cookies.clear()

    response = client.post(
        "/api/v1/auth/login",
        json={"email": "admin@example.com", "password": "wrong-password"},
    )

    assert response.status_code == 401
