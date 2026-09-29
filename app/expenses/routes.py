from datetime import date

from flask import Blueprint, flash, redirect, render_template, request, url_for
from flask_login import current_user, login_required

from ..extensions import db
from ..forms import ValidationError, clean_text, parse_date, parse_money
from ..models import Expense, ExpenseCategory
from ..utils import ensure_default_categories, owned_or_404

expenses_bp = Blueprint("expenses", __name__, url_prefix="/expenses")


def apply_expense(item, categories):
    item.amount = parse_money(request.form.get("amount"))
    item.date = parse_date(request.form.get("date"))
    item.description = clean_text(request.form.get("description"))
    item.payment_method = clean_text(request.form.get("payment_method"), "UPI")[:40]
    try:
        category_id = int(request.form.get("category_id"))
    except (TypeError, ValueError):
        raise ValidationError("Choose a category.")
    if category_id not in {category.id for category in categories}:
        raise ValidationError("Choose one of your categories.")
    item.category_id = category_id


@expenses_bp.get("")
@login_required
def index():
    ensure_default_categories(current_user)
    categories = ExpenseCategory.query.filter_by(user_id=current_user.id, is_active=True).order_by(ExpenseCategory.name).all()
    query = Expense.query.filter_by(user_id=current_user.id)
    category_id = request.args.get("category_id", type=int)
    from_date = request.args.get("from")
    to_date = request.args.get("to")
    if category_id:
        query = query.filter_by(category_id=category_id)
    if from_date:
        query = query.filter(Expense.date >= from_date)
    if to_date:
        query = query.filter(Expense.date <= to_date)
    expenses = query.order_by(Expense.date.desc(), Expense.id.desc()).all()
    return render_template("expenses/list.html", expenses=expenses, categories=categories, selected_category=category_id, from_date=from_date, to_date=to_date)


@expenses_bp.route("/add", methods=["GET", "POST"])
@login_required
def add():
    ensure_default_categories(current_user)
    categories = ExpenseCategory.query.filter_by(user_id=current_user.id, is_active=True).order_by(ExpenseCategory.name).all()
    item = Expense(user_id=current_user.id, date=date.today(), payment_method="UPI")
    if request.method == "POST":
        try:
            apply_expense(item, categories)
            db.session.add(item)
            db.session.commit()
            flash("Expense added.", "success")
            return redirect(url_for("expenses.index"))
        except ValidationError as error:
            db.session.rollback()
            flash(str(error), "error")
    return render_template("expenses/form.html", item=item, categories=categories, title="Add expense")


@expenses_bp.route("/<int:record_id>/edit", methods=["GET", "POST"])
@login_required
def edit(record_id):
    ensure_default_categories(current_user)
    categories = ExpenseCategory.query.filter_by(user_id=current_user.id, is_active=True).order_by(ExpenseCategory.name).all()
    item = owned_or_404(Expense, record_id, current_user.id)
    if request.method == "POST":
        try:
            apply_expense(item, categories)
            db.session.commit()
            flash("Expense updated.", "success")
            return redirect(url_for("expenses.index"))
        except ValidationError as error:
            db.session.rollback()
            flash(str(error), "error")
    return render_template("expenses/form.html", item=item, categories=categories, title="Edit expense")


@expenses_bp.post("/<int:record_id>/delete")
@login_required
def delete(record_id):
    item = owned_or_404(Expense, record_id, current_user.id)
    db.session.delete(item)
    db.session.commit()
    flash("Expense removed.", "info")
    return redirect(url_for("expenses.index"))


@expenses_bp.post("/categories/add")
@login_required
def add_category():
    name = clean_text(request.form.get("name"))[:80]
    if not name:
        flash("Add a category name first.", "error")
    elif ExpenseCategory.query.filter_by(user_id=current_user.id, name=name).first():
        flash("That category already exists.", "info")
    else:
        db.session.add(ExpenseCategory(user_id=current_user.id, name=name, is_default=False))
        db.session.commit()
        flash("Custom category added.", "success")
    return redirect(url_for("expenses.index"))
