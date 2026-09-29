from datetime import date

from flask import Blueprint, flash, redirect, render_template, request, url_for
from flask_login import current_user, login_required

from ..extensions import db
from ..forms import ValidationError, clean_text, parse_date, parse_money
from ..models import Income
from ..utils import owned_or_404

income_bp = Blueprint("income", __name__, url_prefix="/income")


def apply_income(item):
    item.source_name = clean_text(request.form.get("source_name"))
    item.amount = parse_money(request.form.get("amount"))
    item.date = parse_date(request.form.get("date"))
    item.notes = clean_text(request.form.get("notes"))
    if not item.source_name:
        raise ValidationError("Add a name for this income source.")


@income_bp.get("")
@login_required
def index():
    incomes = Income.query.filter_by(user_id=current_user.id).order_by(Income.date.desc(), Income.id.desc()).all()
    return render_template("income/list.html", incomes=incomes)


@income_bp.route("/add", methods=["GET", "POST"])
@login_required
def add():
    item = Income(user_id=current_user.id, date=date.today())
    if request.method == "POST":
        try:
            apply_income(item)
            db.session.add(item)
            db.session.commit()
            flash("Income added.", "success")
            return redirect(url_for("income.index"))
        except ValidationError as error:
            db.session.rollback()
            flash(str(error), "error")
    return render_template("income/form.html", item=item, title="Add income")


@income_bp.route("/<int:record_id>/edit", methods=["GET", "POST"])
@login_required
def edit(record_id):
    item = owned_or_404(Income, record_id, current_user.id)
    if request.method == "POST":
        try:
            apply_income(item)
            db.session.commit()
            flash("Income updated.", "success")
            return redirect(url_for("income.index"))
        except ValidationError as error:
            db.session.rollback()
            flash(str(error), "error")
    return render_template("income/form.html", item=item, title="Edit income")


@income_bp.post("/<int:record_id>/delete")
@login_required
def delete(record_id):
    item = owned_or_404(Income, record_id, current_user.id)
    db.session.delete(item)
    db.session.commit()
    flash("Income removed.", "info")
    return redirect(url_for("income.index"))
