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
