from .conftest import login


def test_dashboard_contains_summary_and_chart_payload(client):
    login(client)
    client.post("/income/add", data={"source_name": "Salary", "amount": "50000", "date": "2026-09-01", "notes": ""})
    response = client.post("/expenses/add", data={"amount": "1200", "date": "2026-09-02", "category_id": "1", "description": "Rent", "payment_method": "UPI"})
    assert response.status_code == 302
    response = client.get("/dashboard?month=2026-09")
    assert response.status_code == 200
    assert b"Income vs. expenses" in response.data
    assert b"trendChart" in response.data
    assert b"Health score" in response.data
