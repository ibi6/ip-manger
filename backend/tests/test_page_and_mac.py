from tests.conftest import auth_header


def test_ip_page(client):
    h = auth_header(client, "admin")
    r = client.get("/api/v1/ip-addresses/page?page=1&page_size=10", headers=h)
    assert r.status_code == 200
    body = r.json()
    assert "items" in body and "total" in body
    assert body["page"] == 1
    assert len(body["items"]) <= 10


def test_mac_unique(client):
    h = auth_header(client, "admin")
    r1 = client.post(
        "/api/v1/devices",
        headers=h,
        json={"name": "A", "device_type": "pc", "mac": "AA:BB:CC:11:22:33"},
    )
    assert r1.status_code == 201
    r2 = client.post(
        "/api/v1/devices",
        headers=h,
        json={"name": "B", "device_type": "pc", "mac": "AA:BB:CC:11:22:33"},
    )
    assert r2.status_code == 400


def test_create_department(client):
    h = auth_header(client, "admin")
    r = client.post(
        "/api/v1/users/departments",
        headers=h,
        json={"name": "测试部", "code": "TEST"},
    )
    assert r.status_code == 201
    assert r.json()["code"] == "TEST"
