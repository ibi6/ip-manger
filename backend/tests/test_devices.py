from tests.conftest import auth_header


def test_create_and_list_device(client):
    h = auth_header(client, "admin")
    r = client.post(
        "/api/v1/devices",
        headers=h,
        json={"name": "测试电脑", "device_type": "pc", "mac": "AA:BB:CC:DD:EE:11"},
    )
    assert r.status_code == 201, r.text
    assert r.json()["name"] == "测试电脑"

    r2 = client.get("/api/v1/devices", headers=h)
    assert r2.status_code == 200
    assert any(d["name"] == "测试电脑" for d in r2.json())


def test_viewer_cannot_create_device(client):
    h = auth_header(client, "viewer")
    r = client.post(
        "/api/v1/devices",
        headers=h,
        json={"name": "x", "device_type": "pc"},
    )
    assert r.status_code == 403


def test_update_device(client):
    h = auth_header(client, "admin")
    created = client.post(
        "/api/v1/devices",
        headers=h,
        json={"name": "旧名", "device_type": "pc"},
    ).json()
    r = client.patch(
        f"/api/v1/devices/{created['id']}",
        headers=h,
        json={"name": "新名", "location": "3F"},
    )
    assert r.status_code == 200
    assert r.json()["name"] == "新名"
    assert r.json()["location"] == "3F"


def test_export_devices_csv(client):
    h = auth_header(client, "admin")
    r = client.get("/api/v1/io/export/devices", headers=h)
    assert r.status_code == 200
    assert "text/csv" in r.headers.get("content-type", "")
    assert b"name" in r.content or "name" in r.text
