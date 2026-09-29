from .conftest import login


def test_report_exports(client):
    login(client)
    response = client.get("/reports/2026-09")
    assert response.status_code == 200
    assert b"Monthly report" in response.data
    csv_response = client.get("/reports/2026-09/csv")
    assert csv_response.status_code == 200
    assert "text/csv" in csv_response.headers["Content-Type"]
    assert b"Net savings" in csv_response.data
    pdf_response = client.get("/reports/2026-09/pdf")
    assert pdf_response.status_code == 200
    assert pdf_response.data.startswith(b"%PDF")
