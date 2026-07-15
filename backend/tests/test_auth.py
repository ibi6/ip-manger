from tests.conftest import auth_header


def test_login_ok(client):
    r = client.post("/api/v1/auth/login", json={"username": "admin", "password": "ChangeMe123!"})
    assert r.status_code == 200
    assert "access_token" in r.json()


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


def test_login_rate_limit(client):
    # exhaust limit
    for _ in range(8):
        client.post("/api/v1/auth/login", json={"username": "admin", "password": "wrong"})
    r = client.post("/api/v1/auth/login", json={"username": "admin", "password": "wrong"})
    assert r.status_code == 429
