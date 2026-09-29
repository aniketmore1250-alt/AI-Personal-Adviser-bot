from .conftest import login


def test_income_add_edit_delete(client, app):
    login(client)
    response = client.post("/income/add", data={"source_name": "Freelance", "amount": "12000", "date": "2026-09-10", "notes": "Client A"}, follow_redirects=True)
    assert response.status_code == 200
    assert b"Freelance" in response.data
    from app.models import Income
    with app.app_context():
        item = Income.query.filter_by(source_name="Freelance").first()
        item_id = item.id
    response = client.post(f"/income/{item_id}/edit", data={"source_name": "Client A", "amount": "15000", "date": "2026-09-10", "notes": "Updated"}, follow_redirects=True)
    assert b"Client A" in response.data
    response = client.post(f"/income/{item_id}/delete", follow_redirects=True)
    assert b"Nothing recorded yet" in response.data


def test_income_isolation(client, app):
    login(client)
    from app.extensions import db
    from app.models import User, Income
    with app.app_context():
        other = User(name="Other", email="other@example.com", monthly_income=1)
        other.set_password("Password123")
        db.session.add(other)
        db.session.flush()
        item = Income(user_id=other.id, source_name="Private", amount=20, date=__import__("datetime").date(2026, 9, 1))
        db.session.add(item)
        db.session.commit()
        item_id = item.id
    assert client.get(f"/income/{item_id}/edit").status_code == 404
