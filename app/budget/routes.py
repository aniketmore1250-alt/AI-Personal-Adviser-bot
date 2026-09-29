from flask import Blueprint, flash, redirect, render_template, request, url_for
from flask_login import current_user, login_required

from ..extensions import db
from ..services.ai_service import generate_recommendation
from ..services.analytics import summary_for_user
from ..services.budget_engine import generate_rule_based_budget, save_budget_plan
from ..utils import ensure_default_categories, selected_month

budget_bp = Blueprint("budget", __name__, url_prefix="/budget")


@budget_bp.get("")
@login_required
def index():
    ensure_default_categories(current_user)
    month = selected_month()
    plan = generate_rule_based_budget(current_user, month)
    summary = summary_for_user(current_user, month)
    return render_template("budget/index.html", month=month, plan=plan, summary=summary)


@budget_bp.post("/save")
@login_required
def save():
    month = selected_month()
    allocations = []
    for key, value in request.form.items():
        if key.startswith("budget_"):
            try:
                amount = float(value or 0)
            except ValueError:
                amount = -1
            allocations.append({"category": key.removeprefix("budget_"), "amount": amount})
    save_budget_plan(current_user, month, allocations, source="manual")
    flash("Your budget limits were saved.", "success")
    return redirect(url_for("budget.index", month=month))


@budget_bp.post("/generate")
@login_required
def generate():
    month = selected_month()
    payload, _ = generate_recommendation(current_user, month, kind="budget")
    budget = payload.get("budget") or {}
    allocations = budget.get("allocations") if isinstance(budget, dict) else None
    if not isinstance(allocations, list) or not allocations:
        allocations = generate_rule_based_budget(current_user, month)["allocations"]
    save_budget_plan(current_user, month, allocations, source=payload.get("source_note", "ai")[:20])
    flash("A personalized budget is ready. Review the limits below and adjust anything that does not fit.", "success")
    return redirect(url_for("budget.index", month=month))
