from .conftest import login


def test_budget_generation_and_manual_save(client, app):
    login(client)
    response = client.post("/budget/generate?month=2026-09", follow_redirects=True)
    assert response.status_code == 200
    assert b"Category limits" in response.data
    from app.models import Budget
    with app.app_context():
        assert Budget.query.filter_by(month="2026-09").count() > 0
    response = client.post("/budget/save?month=2026-09", data={"budget_Rent": "12000", "budget_Food": "5000"}, follow_redirects=True)
    assert b"limits were saved" in response.data


def test_rule_budget_reads_history_and_goals(app):
    from datetime import date
    from app.extensions import db
    from app.models import Expense, ExpenseCategory, User
    from app.services.budget_engine import generate_rule_based_budget
    with app.app_context():
        user = User.query.filter_by(email="alice@example.com").first()
        user.savings_target = 120000
        user.financial_goals = "Build an emergency fund"
        food = ExpenseCategory.query.filter_by(user_id=user.id, name="Food").first()
        db.session.add_all([
            Expense(user_id=user.id, category_id=food.id, amount=6000, date=date(2026, 8, 10)),
            Expense(user_id=user.id, category_id=food.id, amount=6500, date=date(2026, 9, 10)),
        ])
        db.session.commit()
        plan = generate_rule_based_budget(user, "2026-09")
        assert plan["history_averages"]["Food"] > 0
        assert plan["goal_bonus"] > 0
