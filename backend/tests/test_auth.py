import pytest

from app.core.security import decode_token
from tests.conftest import auth_header


def test_login_ok(client):
    r = client.post("/api/v1/auth/login", json={"username": "admin", "password": "ChangeMe123!"})
    assert r.status_code == 200
    assert "access_token" in r.json()


def test_login_token_has_traceable_identity(client):
    response = client.post(
        "/api/v1/auth/login",
        json={"username": "admin", "password": "ChangeMe123!"},
    )

    payload = decode_token(response.json()["access_token"])

    assert payload["sub"] == "admin"
    assert isinstance(payload["ver"], int)
    assert isinstance(payload["iat"], int)
    assert isinstance(payload["jti"], str)
    assert len(payload["jti"]) >= 16


def test_decode_rejects_damaged_token():
    with pytest.raises(ValueError, match="invalid token"):
        decode_token("not-a-jwt")


def test_login_bad_password(client):
    r = client.post("/api/v1/auth/login", json={"username": "admin", "password": "wrong"})
    assert r.status_code == 401


def test_me(client):
    h = auth_header(client)
    r = client.get("/api/v1/auth/me", headers=h)
    assert r.status_code == 200
    assert r.json()["username"] == "admin"
    assert r.json()["role"] == "admin"


def test_unauthorized(client):
    r = client.get("/api/v1/auth/me")
    assert r.status_code == 401


def test_logout_revokes_current_token(client):
    login = client.post(
        "/api/v1/auth/login",
        json={"username": "viewer", "password": "ChangeMe123!"},
    )
    headers = {"Authorization": f"Bearer {login.json()['access_token']}"}

    logout = client.post("/api/v1/auth/logout", headers=headers)

    assert logout.status_code == 200
    assert client.get("/api/v1/auth/me", headers=headers).status_code == 401


def test_login_rate_limit(client):
    # exhaust limit
    for _ in range(8):
        client.post("/api/v1/auth/login", json={"username": "admin", "password": "wrong"})
    r = client.post("/api/v1/auth/login", json={"username": "admin", "password": "wrong"})
    assert r.status_code == 429


def test_successful_logins_do_not_consume_failure_budget(client):
    """Valid credentials must never be treated as brute-force failures."""
    for _ in range(12):
        response = client.post(
            "/api/v1/auth/login",
            json={"username": "admin", "password": "ChangeMe123!"},
        )
        assert response.status_code == 200, response.text


def test_successful_login_clears_previous_failures(client):
    """A real user who recovers their password should receive a fresh budget."""
    for _ in range(7):
        response = client.post(
            "/api/v1/auth/login",
            json={"username": "admin", "password": "wrong"},
        )
        assert response.status_code == 401

    recovered = client.post(
        "/api/v1/auth/login",
        json={"username": "admin", "password": "ChangeMe123!"},
    )
    assert recovered.status_code == 200

    for _ in range(7):
        response = client.post(
            "/api/v1/auth/login",
            json={"username": "admin", "password": "wrong"},
        )
        assert response.status_code == 401
