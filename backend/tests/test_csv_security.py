from app.api.v1.io_csv import MAX_CSV_BYTES, _safe_csv_cell
from tests.conftest import auth_header


def test_csv_export_neutralizes_spreadsheet_formulas():
    assert _safe_csv_cell('=HYPERLINK("https://example.invalid")').startswith("'")
    assert _safe_csv_cell(" +SUM(1,2)").lstrip().startswith("'")
    assert _safe_csv_cell("normal value") == "normal value"


def test_csv_import_rejects_oversized_upload(client):
    response = client.post(
        "/api/v1/io/import/subnets",
        headers=auth_header(client),
        files={"file": ("subnets.csv", b"x" * (MAX_CSV_BYTES + 1), "text/csv")},
    )

    assert response.status_code == 413


def test_department_exports_do_not_leak_other_departments(client):
    admin = auth_header(client, "admin")
    biz = auth_header(client, "biz")
    all_subnets = client.get("/api/v1/subnets", headers=admin).json()
    other = next(subnet for subnet in all_subnets if subnet["department_name"] != "研发中心")
    other_ip = client.get(
        f"/api/v1/ip-addresses?subnet_id={other['id']}&page_size=1",
        headers=admin,
    ).json()[0]

    subnet_export = client.get("/api/v1/io/export/subnets", headers=biz)
    ip_export = client.get("/api/v1/io/export/ip-addresses", headers=biz)

    assert subnet_export.status_code == 200
    assert ip_export.status_code == 200
    assert other["cidr"] not in subnet_export.text
    assert other_ip["address"] not in ip_export.text
