from datetime import date

from flask import Blueprint, flash, redirect, render_template, request, url_for
from flask_login import current_user, login_required

from ..extensions import db
from ..forms import ValidationError, clean_text, parse_date, parse_money
from ..models import SavingsGoal
from ..utils import owned_or_404

goals_bp = Blueprint("goals", __name__, url_prefix="/goals")


def apply_goal(item):
    item.name = clean_text(request.form.get("name"))
    item.target_amount = parse_money(request.form.get("target_amount"))
    item.current_amount = parse_money(request.form.get("current_amount", "0"), allow_zero=True)
    deadline = request.form.get("deadline")
    item.deadline = parse_date(deadline) if deadline else None
    if not item.name:
        raise ValidationError("Name this goal so it is easy to recognize.")
    item.status = "complete" if item.current_amount >= item.target_amount else "active"


@goals_bp.get("")
@login_required
def index():
    goals = SavingsGoal.query.filter_by(user_id=current_user.id).order_by(SavingsGoal.status, SavingsGoal.deadline).all()
    return render_template("goals/index.html", goals=goals)


@goals_bp.route("/add", methods=["GET", "POST"])
@login_required
def add():
    item = SavingsGoal(user_id=current_user.id, deadline=date.today())
    if request.method == "POST":
        try:
            apply_goal(item)
            db.session.add(item)
            db.session.commit()
            flash("Savings goal added.", "success")
            return redirect(url_for("goals.index"))
        except ValidationError as error:
            db.session.rollback()
            flash(str(error), "error")
    return render_template("goals/form.html", item=item, title="Add savings goal")


@goals_bp.route("/<int:record_id>/edit", methods=["GET", "POST"])
@login_required
def edit(record_id):
    item = owned_or_404(SavingsGoal, record_id, current_user.id)
    if request.method == "POST":
        try:
            apply_goal(item)
            db.session.commit()
            flash("Savings goal updated.", "success")
            return redirect(url_for("goals.index"))
        except ValidationError as error:
            db.session.rollback()
            flash(str(error), "error")
    return render_template("goals/form.html", item=item, title="Edit savings goal")


@goals_bp.post("/<int:record_id>/delete")
@login_required
def delete(record_id):
    item = owned_or_404(SavingsGoal, record_id, current_user.id)
    db.session.delete(item)
    db.session.commit()
    flash("Savings goal removed.", "info")
    return redirect(url_for("goals.index"))
