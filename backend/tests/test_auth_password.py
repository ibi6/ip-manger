from tests.conftest import auth_header


def test_change_password(client):
    h = auth_header(client, "viewer")
    r = client.post(
        "/api/v1/auth/change-password",
        headers=h,
        json={"old_password": "ChangeMe123!", "new_password": "NewPass99"},
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
        json={"username": "viewer", "password": "NewPass99"},
    )
    assert ok.status_code == 200


def test_change_password_wrong_old(client):
    h = auth_header(client, "biz")
    r = client.post(
        "/api/v1/auth/change-password",
        headers=h,
        json={"old_password": "wrong-old", "new_password": "NewPass99"},
    )
    assert r.status_code == 400
