import pytest

from app import create_app
from app.extensions import db
from app.models import ExpenseCategory, User


@pytest.fixture()
def app(tmp_path):
    application = create_app({
        "TESTING": True,
        "WTF_CSRF_ENABLED": False,
        "SECRET_KEY": "test-secret",
        "SQLALCHEMY_DATABASE_URI": f"sqlite:///{tmp_path / 'test.db'}",
        "AI_PROVIDER": "rules",
    })
    with application.app_context():
        db.drop_all()
        db.create_all()
        user = User(name="Alice Example", email="alice@example.com", monthly_income=50000, currency="INR", user_type="salaried")
        user.set_password("Password123")
        db.session.add(user)
        db.session.flush()
        for name in ["Rent", "Food", "Transport", "Utilities", "Groceries", "Savings", "Other"]:
            db.session.add(ExpenseCategory(user_id=user.id, name=name, is_default=True))
        db.session.commit()
    yield application
    with application.app_context():
        db.session.remove()
        db.drop_all()


@pytest.fixture()
def client(app):
    return app.test_client()


@pytest.fixture()
def csrf_app(tmp_path):
    application = create_app({
        "TESTING": True,
        "WTF_CSRF_ENABLED": True,
        "SECRET_KEY": "csrf-test-secret",
        "SQLALCHEMY_DATABASE_URI": f"sqlite:///{tmp_path / 'csrf-test.db'}",
        "AI_PROVIDER": "rules",
        "SESSION_COOKIE_SAMESITE": "None",
        "SESSION_COOKIE_SECURE": True,
    })
    with application.app_context():
        db.create_all()
    yield application
    with application.app_context():
        db.session.remove()
        db.drop_all()


@pytest.fixture()
def csrf_client(csrf_app):
    return csrf_app.test_client()


def login(client):
    return client.post("/login", data={"email": "alice@example.com", "password": "Password123"}, follow_redirects=True)
