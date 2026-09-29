from collections import defaultdict

from sqlalchemy import func

from ..extensions import db
from ..models import Budget, Expense, ExpenseCategory, Income
from .analytics import month_bounds, money, shift_month


ESSENTIALS = ["Rent", "Utilities", "Groceries", "Food", "Transport", "Healthcare", "Education"]
LIFESTYLE = ["Entertainment", "Shopping", "Other"]
SAVINGS = ["Savings"]


def category_for(user, name):
    category = ExpenseCategory.query.filter_by(user_id=user.id, name=name).first()
    if not category:
        category = ExpenseCategory(user_id=user.id, name=name, is_default=name in ESSENTIALS + LIFESTYLE + SAVINGS)
        db.session.add(category)
        db.session.flush()
    return category


def income_basis(user, month):
    start, end = month_bounds(month)
    actual = db.session.query(func.sum(Income.amount)).filter(Income.user_id == user.id, Income.date >= start, Income.date <= end).scalar()
    return money(actual or user.monthly_income)


def recent_category_averages(user, month):
    start, _ = month_bounds(shift_month(month, -2))
    _, end = month_bounds(month)
    rows = (
        Expense.query.join(ExpenseCategory)
        .filter(Expense.user_id == user.id, Expense.date >= start, Expense.date <= end)
        .with_entities(ExpenseCategory.name, func.sum(Expense.amount))
        .group_by(ExpenseCategory.name)
        .all()
    )
    return {name: money(total) / 3 for name, total in rows}


def generate_rule_based_budget(user, month):
    income = income_basis(user, month)
    user_type = (user.user_type or "salaried").lower()
    shares = {
        "student": {"essentials": 0.65, "lifestyle": 0.15, "savings": 0.20},
        "freelancer": {"essentials": 0.50, "lifestyle": 0.20, "savings": 0.30},
        "household": {"essentials": 0.60, "lifestyle": 0.20, "savings": 0.20},
        "salaried": {"essentials": 0.50, "lifestyle": 0.30, "savings": 0.20},
    }.get(user_type, {"essentials": 0.50, "lifestyle": 0.30, "savings": 0.20})
    history = recent_category_averages(user, month)
    goals_text = (user.financial_goals or "").lower()
    goal_bonus = 0
    if user.savings_target:
        goal_bonus = min(income * 0.05, float(user.savings_target) / 12)
    if "emergency" in goals_text:
        goal_bonus = max(goal_bonus, income * 0.03)
    savings_total = min(income * 0.35, income * shares["savings"] + goal_bonus)
    bucket_totals = {
        "essentials": income * shares["essentials"],
        "lifestyle": max(0, income - income * shares["essentials"] - savings_total),
        "savings": savings_total,
    }
    weights = {"Rent": .30, "Food": .17, "Groceries": .16, "Transport": .10, "Utilities": .08, "Healthcare": .08, "Education": .06, "Entertainment": .45, "Shopping": .35, "Other": .20, "Savings": 1.0}
    allocations = []
    for bucket, names in (("essentials", ESSENTIALS), ("lifestyle", LIFESTYLE), ("savings", SAVINGS)):
        bucket_total = bucket_totals[bucket]
        bucket_weight = sum(weights[name] for name in names)
        proposed = []
        for name in names:
            baseline = bucket_total * weights[name] / bucket_weight if bucket_weight else 0
            average = history.get(name)
            if average:
                baseline = max(baseline * 0.75, min(baseline * 1.35, average * 1.05))
            proposed.append((name, baseline))
        proposed_total = sum(amount for _, amount in proposed) or 1
        for name, amount in proposed:
            allocations.append({"category": name, "amount": round(amount / proposed_total * bucket_total, 2), "bucket": bucket})
    return {"month": month, "income_basis": income, "shares": {**shares, "savings": round(savings_total / income, 4) if income else 0}, "history_averages": history, "goal_bonus": round(goal_bonus, 2), "allocations": allocations, "source": "rules"}


def save_budget_plan(user, month, allocations, source="manual"):
    saved = []
    for item in allocations:
        name = str(item.get("category", "Other")).strip()[:80]
        amount = round(float(item.get("amount", 0) or 0), 2)
        if not name or amount < 0:
            continue
        category = category_for(user, name)
        budget = Budget.query.filter_by(user_id=user.id, category_id=category.id, month=month).first()
        if not budget:
            budget = Budget(user_id=user.id, category_id=category.id, month=month)
            db.session.add(budget)
        budget.limit_amount = amount
        budget.source = source
        saved.append(budget)
    db.session.commit()
    return saved
