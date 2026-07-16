from tests.conftest import auth_header


def test_change_password(client):
    h = auth_header(client, "viewer")
    r = client.post(
        "/api/v1/auth/change-password",
        headers=h,
        json={"old_password": "ChangeMe123!", "new_password": "NewSecurePass99!"},
    )
    assert r.status_code == 200, r.text

    # 旧密码不能再登录
    bad = client.post(
        "/api/v1/auth/login",
        json={"username": "viewer", "password": "ChangeMe123!"},
    )
    assert bad.status_code == 401

    ok = client.post(
        "/api/v1/auth/login",
        json={"username": "viewer", "password": "NewSecurePass99!"},
    )
    assert ok.status_code == 200


def test_change_password_wrong_old(client):
    h = auth_header(client, "biz")
    r = client.post(
        "/api/v1/auth/change-password",
        headers=h,
        json={"old_password": "wrong-old", "new_password": "NewSecurePass99!"},
    )
    assert r.status_code == 400


def test_old_token_is_rejected_after_password_change(client):
    """Changing a password must revoke tokens issued with the old credential state."""
    old_header = auth_header(client, "viewer")
    changed = client.post(
        "/api/v1/auth/change-password",
        headers=old_header,
        json={
            "old_password": "ChangeMe123!",
            "new_password": "AnotherSecure99!",
        },
    )
    assert changed.status_code == 200, changed.text

    old_session = client.get("/api/v1/auth/me", headers=old_header)
    assert old_session.status_code == 401


def test_weak_new_password_is_rejected(client):
    """Length alone is insufficient for a production password."""
    response = client.post(
        "/api/v1/auth/change-password",
        headers=auth_header(client),
        json={"old_password": "ChangeMe123!", "new_password": "allletterslong"},
    )
    assert response.status_code == 422
