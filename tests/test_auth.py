import re

from .conftest import login


def test_registration_login_logout_and_protected_route(client):
    response = client.get("/dashboard")
    assert response.status_code == 302
    response = client.post("/register", data={"name": "New User", "email": "new@example.com", "password": "Password123", "confirm_password": "Password123", "monthly_income": "40000", "currency": "INR", "user_type": "student"}, follow_redirects=True)
    assert response.status_code == 200
    assert b"Good to see you" in response.data
    logout = client.post("/logout", follow_redirects=True)
    assert b"Personal finance" in logout.data
    logged_in = login(client)
    assert b"Dashboard" in logged_in.data


def test_bad_login_is_friendly(client):
    response = client.post("/login", data={"email": "alice@example.com", "password": "wrong"})
    assert response.status_code == 200
    assert b"could not match" in response.data


def test_preview_registration_preserves_csrf_session(csrf_client, csrf_app):
    preview_origin = "https://preview.example"
    response = csrf_client.get("/register", base_url=preview_origin)
    token = re.search(r'name="csrf_token" value="([^"]+)"', response.get_data(as_text=True)).group(1)
    cookies = "\n".join(response.headers.getlist("Set-Cookie"))
    assert token
    assert "SameSite=None" in cookies
    assert "Secure" in cookies
    assert "HttpOnly" in cookies
    # Werkzeug's test cookie jar intentionally does not retain Secure cookies;
    # the managed Preview browser does, so resend the captured value explicitly.
    session_value = response.headers.getlist("Set-Cookie")[0].split(";", 1)[0].split("=", 1)[1]
    csrf_client.set_cookie("session", session_value, domain="preview.example", secure=False)

    response = csrf_client.post("/register", base_url=preview_origin, data={
        "csrf_token": token,
        "name": "Preview User",
        "email": "preview@example.com",
        "password": "Password123",
        "confirm_password": "Password123",
        "monthly_income": "50000",
        "currency": "INR",
        "user_type": "salaried",
    }, headers={"Referer": f"{preview_origin}/register"})
    assert response.status_code == 302
    assert response.headers["Location"].endswith("/dashboard")
    with csrf_app.app_context():
        from app.models import User
        assert User.query.filter_by(email="preview@example.com").first() is not None


def test_preview_registration_without_csrf_is_rejected(csrf_client):
    response = csrf_client.post("/register", base_url="https://preview.example", data={
        "name": "Missing Token",
        "email": "missing@example.com",
        "password": "Password123",
        "confirm_password": "Password123",
    })
    assert response.status_code == 400
