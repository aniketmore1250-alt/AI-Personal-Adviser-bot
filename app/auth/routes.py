from flask import Blueprint, flash, redirect, render_template, request, url_for
from flask_login import current_user, login_required, login_user, logout_user

from ..extensions import db
from ..forms import ValidationError, clean_text, parse_money, safe_next_url
from ..models import ExpenseCategory, User
from ..utils import ensure_default_categories

auth_bp = Blueprint("auth", __name__)


@auth_bp.get("/")
def landing():
    return render_template("landing.html")


@auth_bp.get("/sitemap.xml")
def sitemap():
    pages = ["/", "/login", "/register"]
    body = "<?xml version=\"1.0\" encoding=\"UTF-8\"?>" + "<urlset xmlns=\"http://www.sitemaps.org/schemas/sitemap/0.9\">" + "".join(f"<url><loc>{request.url_root.rstrip('/')}{page}</loc></url>" for page in pages) + "</urlset>"
    return body, 200, {"Content-Type": "application/xml; charset=utf-8"}


@auth_bp.get("/robots.txt")
def robots():
    return f"User-agent: *\nAllow: /\nDisallow: /dashboard\nDisallow: /api/\nSitemap: {request.url_root.rstrip('/')}/sitemap.xml\n", 200, {"Content-Type": "text/plain; charset=utf-8"}


@auth_bp.route("/login", methods=["GET", "POST"])
def login():
    if current_user.is_authenticated:
        return redirect(url_for("dashboard.index"))
    if request.method == "POST":
        email = clean_text(request.form.get("email")).lower()
        password = request.form.get("password", "")
        user = User.query.filter_by(email=email).first()
        if user and user.check_password(password):
            login_user(user, remember=request.form.get("remember") == "on")
            flash("Welcome back. Your money snapshot is ready.", "success")
            return redirect(safe_next_url(request.args.get("next")) or url_for("dashboard.index"))
        flash("We could not match those details. Try again or create an account.", "error")
    return render_template("auth/login.html")


@auth_bp.route("/register", methods=["GET", "POST"])
def register():
    if current_user.is_authenticated:
        return redirect(url_for("dashboard.index"))
    if request.method == "POST":
        name = clean_text(request.form.get("name"))
        email = clean_text(request.form.get("email")).lower()
        password = request.form.get("password", "")
        confirm = request.form.get("confirm_password", "")
        try:
            if len(name) < 2:
                raise ValidationError("Please enter your name.")
            if "@" not in email or "." not in email.split("@")[-1]:
                raise ValidationError("Enter a valid email address.")
            if len(password) < 8:
                raise ValidationError("Use at least 8 characters for your password.")
            if password != confirm:
                raise ValidationError("Passwords do not match.")
            if User.query.filter_by(email=email).first():
                raise ValidationError("An account with that email already exists.")
            user = User(name=name, email=email, user_type=request.form.get("user_type", "salaried"))
            user.monthly_income = parse_money(request.form.get("monthly_income", "0"), allow_zero=True)
            user.currency = request.form.get("currency", "INR")[:8]
            user.set_password(password)
            db.session.add(user)
            db.session.flush()
            db.session.commit()
            ensure_default_categories(user)
            login_user(user)
            flash("Your account is ready. Let’s make a plan that feels doable.", "success")
            return redirect(url_for("dashboard.index"))
        except ValidationError as error:
            db.session.rollback()
            flash(str(error), "error")
    return render_template("auth/register.html")


@auth_bp.post("/logout")
@login_required
def logout():
    logout_user()
    flash("You have been safely logged out.", "info")
    return redirect(url_for("auth.landing"))
