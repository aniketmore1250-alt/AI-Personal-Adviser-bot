from calendar import monthrange
from datetime import date

from sqlalchemy import func

from ..models import Budget, Expense, ExpenseCategory, Income, SavingsGoal


def shift_month(month, delta):
    year, value = [int(part) for part in month.split("-")]
    value += delta
    while value < 1:
        year -= 1
        value += 12
    while value > 12:
        year += 1
        value -= 12
    return f"{year:04d}-{value:02d}"


def month_bounds(month):
    year, value = [int(part) for part in month.split("-")]
    return date(year, value, 1), date(year, value, monthrange(year, value)[1])


def money(value):
    return round(float(value or 0), 2)


def health_score(summary):
    income = summary["income_total"]
    expenses = summary["expense_total"]
    savings_rate = summary["savings_rate"]
    budget_utilization = summary["budget_utilization"]
    emergency_progress = summary["emergency_fund"]["progress"]
    score = 35
    score += min(30, max(0, savings_rate) * 0.75)
    score += max(0, min(20, 20 - max(0, budget_utilization - 80) * 0.5))
    score += min(15, emergency_progress * 0.15)
    if income <= 0:
        score -= 15
    if expenses > income and income > 0:
        score -= 15
    return max(0, min(100, round(score)))


def summary_for_user(user, month):
    start, end = month_bounds(month)
    income_total = money(
        Income.query.filter(Income.user_id == user.id, Income.date >= start, Income.date <= end)
        .with_entities(func.sum(Income.amount)).scalar()
    )
    expense_total = money(
        Expense.query.filter(Expense.user_id == user.id, Expense.date >= start, Expense.date <= end)
        .with_entities(func.sum(Expense.amount)).scalar()
    )
    category_rows = (
        Expense.query.join(ExpenseCategory)
        .filter(Expense.user_id == user.id, Expense.date >= start, Expense.date <= end)
        .with_entities(ExpenseCategory.name, func.sum(Expense.amount))
        .group_by(ExpenseCategory.name)
        .order_by(func.sum(Expense.amount).desc())
        .all()
    )
    category_totals = {name: money(total) for name, total in category_rows}
    budgets = Budget.query.filter_by(user_id=user.id, month=month).all()
    budget_total = sum(money(item.limit_amount) for item in budgets)
    budget_performance = []
    for item in budgets:
        actual = category_totals.get(item.category.name, 0)
        limit = money(item.limit_amount)
        utilization = round(actual / limit * 100, 1) if limit else 0
        status = "green" if utilization <= 80 else "yellow" if utilization <= 100 else "red"
        budget_performance.append({
            "category": item.category.name,
            "limit": limit,
            "actual": actual,
            "utilization": utilization,
            "status": status,
        })
    income_basis = income_total or money(user.monthly_income)
    savings = round(income_total - expense_total, 2)
    savings_rate = round(savings / income_basis * 100, 1) if income_basis else 0
    budget_utilization = round(expense_total / budget_total * 100, 1) if budget_total else 0
    emergency_target_low = round(expense_total * 3, 2)
    emergency_target_high = round(expense_total * 6, 2)
    emergency_saved = money(sum(float(goal.current_amount or 0) for goal in user.savings_goals))
    emergency_progress = min(100, round(emergency_saved / emergency_target_low * 100, 1)) if emergency_target_low else 0

    trend = []
    for offset in range(-5, 1):
        trend_month = shift_month(month, offset)
        trend_start, trend_end = month_bounds(trend_month)
        trend_income = money(Income.query.filter(Income.user_id == user.id, Income.date >= trend_start, Income.date <= trend_end).with_entities(func.sum(Income.amount)).scalar())
        trend_expenses = money(Expense.query.filter(Expense.user_id == user.id, Expense.date >= trend_start, Expense.date <= trend_end).with_entities(func.sum(Expense.amount)).scalar())
        trend.append({"month": trend_month, "income": trend_income, "expenses": trend_expenses, "savings": round(trend_income - trend_expenses, 2)})

    result = {
        "month": month,
        "income_total": income_total,
        "expense_total": expense_total,
        "net_savings": savings,
        "savings_rate": savings_rate,
        "category_totals": category_totals,
        "budget_total": round(budget_total, 2),
        "budget_utilization": budget_utilization,
        "budget_performance": budget_performance,
        "trend": trend,
        "top_category": next(iter(category_totals.items()), ("None yet", 0)),
        "overspent_categories": [item for item in budget_performance if item["status"] == "red"],
        "emergency_fund": {
            "saved": emergency_saved,
            "target_low": emergency_target_low,
            "target_high": emergency_target_high,
            "progress": emergency_progress,
        },
        "goals": [{"name": goal.name, "progress": goal.progress_percent, "current": money(goal.current_amount), "target": money(goal.target_amount)} for goal in user.savings_goals],
    }
    result["health_score"] = health_score(result)
    result["health_explanation"] = (
        "Your score reflects savings momentum, budget adherence, and emergency-fund progress. "
        "Small, consistent improvements can move it up over time."
    )
    return result
