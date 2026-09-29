from flask import Blueprint, flash, redirect, render_template, request, url_for
from flask_login import current_user, login_required

from ..extensions import db
from ..forms import ValidationError, clean_text, parse_money

profile_bp = Blueprint("profile", __name__, url_prefix="/profile")


@profile_bp.route("", methods=["GET", "POST"])
@login_required
def edit():
    if request.method == "POST":
        try:
            name = clean_text(request.form.get("name"))
            email = clean_text(request.form.get("email")).lower()
            if len(name) < 2 or "@" not in email:
                raise ValidationError("Enter a valid name and email.")
            if current_user.email != email and current_user.__class__.query.filter_by(email=email).first():
                raise ValidationError("That email is already in use.")
            current_user.name = name
            current_user.email = email
            current_user.monthly_income = parse_money(request.form.get("monthly_income", "0"), allow_zero=True)
            current_user.savings_target = parse_money(request.form.get("savings_target", "0"), allow_zero=True)
            current_user.currency = request.form.get("currency", "INR")[:8]
            current_user.user_type = request.form.get("user_type", "salaried")
            current_user.financial_goals = clean_text(request.form.get("financial_goals"))
            db.session.commit()
            flash("Profile updated.", "success")
            return redirect(url_for("profile.edit"))
        except ValidationError as error:
            db.session.rollback()
            flash(str(error), "error")
    return render_template("profile/edit.html")
