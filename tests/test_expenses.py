from .conftest import login


def test_expense_add_filter_and_custom_category(client, app):
    login(client)
    from app.models import ExpenseCategory, Expense
    with app.app_context():
        category = ExpenseCategory.query.filter_by(name="Food").first()
        category_id = category.id
    response = client.post("/expenses/categories/add", data={"name": "Pet care"}, follow_redirects=True)
    assert b"Custom category added" in response.data
    response = client.post("/expenses/add", data={"amount": "850", "date": "2026-09-11", "category_id": str(category_id), "description": "Lunch", "payment_method": "UPI"}, follow_redirects=True)
    assert response.status_code == 200
    assert b"Lunch" in response.data
    response = client.get(f"/expenses?category_id={category_id}")
    assert b"Lunch" in response.data
    with app.app_context():
        item = Expense.query.first()
        item_id = item.id
    response = client.post(f"/expenses/{item_id}/delete", follow_redirects=True)
    assert b"No expenses match" in response.data
