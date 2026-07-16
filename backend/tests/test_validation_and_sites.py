from tests.conftest import auth_header


def test_site_rejects_blank_name_and_invalid_code(client):
    headers = auth_header(client)

    blank_name = client.post(
        "/api/v1/sites",
        headers=headers,
        json={"name": "   ", "code": "NEW", "location": ""},
    )
    invalid_code = client.post(
        "/api/v1/sites",
        headers=headers,
        json={"name": "New Site", "code": "bad code!", "location": ""},
    )

    assert blank_name.status_code == 422
    assert invalid_code.status_code == 422


def test_subnet_rejects_vlan_outside_802_1q_range(client):
    response = client.post(
        "/api/v1/subnets",
        headers=auth_header(client),
        json={
            "name": "Invalid VLAN",
            "cidr": "10.88.1.0/28",
            "site_id": 1,
            "gateway": "10.88.1.1",
            "vlan_id": 4095,
        },
    )

    assert response.status_code == 422


def test_device_rejects_invalid_type_and_oversized_query(client):
    headers = auth_header(client)
    invalid_type = client.post(
        "/api/v1/devices",
        headers=headers,
        json={"name": "x", "device_type": "spaceship"},
    )
    oversized_query = client.get("/api/v1/devices", headers=headers, params={"q": "x" * 101})

    assert invalid_type.status_code == 422
    assert oversized_query.status_code == 422


def test_department_user_cannot_create_device_for_another_department(client):
    response = client.post(
        "/api/v1/devices",
        headers=auth_header(client, "biz"),
        json={"name": "Cross-department device", "device_type": "pc", "department_id": 1},
    )

    assert response.status_code == 403


def test_site_code_is_normalized_before_uniqueness_check(client):
    response = client.post(
        "/api/v1/sites",
        headers=auth_header(client),
        json={"name": "Duplicate HQ", "code": "hq", "location": ""},
    )

    assert response.status_code == 400
    assert "编码已存在" in response.json()["detail"]
