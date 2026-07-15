from tests.conftest import auth_header


def test_disable_and_enable_ip(client):
    h = auth_header(client, "admin")
    subs = client.get("/api/v1/subnets", headers=h).json()
    free = client.get(
        f"/api/v1/ip-addresses?subnet_id={subs[0]['id']}&status=free", headers=h
    ).json()
    target = next(i for i in free if not i["is_network_or_broadcast"])

    r = client.post(f"/api/v1/ip-addresses/{target['id']}/disable", headers=h)
    assert r.status_code == 200, r.text
    assert r.json()["status"] == "disabled"

    r2 = client.post(f"/api/v1/ip-addresses/{target['id']}/enable", headers=h)
    assert r2.status_code == 200
    assert r2.json()["status"] == "free"


def test_allocate_next_free(client):
    h = auth_header(client, "admin")
    # 找一个还有空闲的子网
    subs = client.get("/api/v1/subnets", headers=h).json()
    subnet = next(s for s in subs if s["free_ips"] > 0)
    r = client.post(
        f"/api/v1/subnets/{subnet['id']}/allocate-next",
        headers=h,
        json={"hostname": "next-host", "device_type": "pc"},
    )
    assert r.status_code == 200, r.text
    assert r.json()["status"] == "allocated"
    assert r.json()["hostname"] == "next-host"
