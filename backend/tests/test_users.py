from tests.conftest import auth_header


def test_admin_can_list_and_create_user(client):
    h = auth_header(client, "admin")
    r = client.get("/api/v1/users", headers=h)
    assert r.status_code == 200
    before = len(r.json())

    depts = client.get("/api/v1/users/departments", headers=h).json()
    r2 = client.post(
        "/api/v1/users",
        headers=h,
        json={
            "username": "newuser1",
            "password": "12345678",
            "display_name": "测试用户",
            "role": "viewer",
            "department_id": depts[0]["id"],
        },
    )
    assert r2.status_code == 201, r2.text
    assert r2.json()["username"] == "newuser1"

    r3 = client.get("/api/v1/users", headers=h)
    assert len(r3.json()) == before + 1


def test_non_admin_cannot_manage_users(client):
    h = auth_header(client, "biz")
    r = client.get("/api/v1/users", headers=h)
    assert r.status_code == 403
