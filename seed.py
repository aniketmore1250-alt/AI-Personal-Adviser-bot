from datetime import date
from decimal import Decimal

from app import create_app
from app.extensions import db
from app.models import Expense, ExpenseCategory, Income, SavingsGoal, User
from app.services.budget_engine import generate_rule_based_budget, save_budget_plan
from app.utils import ensure_default_categories

app = create_app()

with app.app_context():
    user = User.query.filter_by(email="demo@financebot.local").first()
    if not user:
        user = User(name="Demo User", email="demo@financebot.local", monthly_income=Decimal("95000"), currency="INR", user_type="salaried", financial_goals="Build an emergency fund and save for a family trip.")
        user.set_password("Demo@12345")
        db.session.add(user)
        db.session.commit()
    ensure_default_categories(user)
    categories = {category.name: category for category in user.categories}
    if Income.query.filter_by(user_id=user.id).count() == 0:
        incomes = [
            ("Salary", 95000, date(2026, 7, 1)), ("Freelance design", 12500, date(2026, 7, 18)),
            ("Salary", 95000, date(2026, 8, 1)), ("Side project", 8000, date(2026, 8, 15)),
            ("Salary", 95000, date(2026, 9, 1)), ("Freelance design", 15000, date(2026, 9, 12)),
        ]
        for source, amount, entry_date in incomes:
            db.session.add(Income(user_id=user.id, source_name=source, amount=amount, date=entry_date))
        expenses = [
            ("Rent", 24000, "Apartment rent", "Bank transfer", date(2026, 7, 3)), ("Food", 6500, "Meals out", "UPI", date(2026, 7, 8)), ("Transport", 3200, "Metro and cabs", "Card", date(2026, 7, 14)), ("Groceries", 7800, "Monthly groceries", "Card", date(2026, 7, 20)), ("Utilities", 4200, "Bills", "UPI", date(2026, 7, 26)), ("Entertainment", 3800, "Weekend plans", "Card", date(2026, 7, 28)),
            ("Rent", 24000, "Apartment rent", "Bank transfer", date(2026, 8, 3)), ("Food", 7200, "Meals out", "UPI", date(2026, 8, 9)), ("Transport", 2800, "Metro and cabs", "Card", date(2026, 8, 16)), ("Groceries", 8200, "Monthly groceries", "Card", date(2026, 8, 20)), ("Utilities", 3900, "Bills", "UPI", date(2026, 8, 25)), ("Shopping", 6400, "Home supplies", "Card", date(2026, 8, 27)),
            ("Rent", 24000, "Apartment rent", "Bank transfer", date(2026, 9, 3)), ("Food", 6100, "Meals out", "UPI", date(2026, 9, 7)), ("Transport", 3100, "Metro and cabs", "Card", date(2026, 9, 15)), ("Groceries", 7900, "Monthly groceries", "Card", date(2026, 9, 19)), ("Utilities", 4100, "Bills", "UPI", date(2026, 9, 24)), ("Education", 3500, "Online course", "Card", date(2026, 9, 26)), ("Entertainment", 2900, "Concert tickets", "Card", date(2026, 9, 28)),
        ]
        for category, amount, description, payment, entry_date in expenses:
            db.session.add(Expense(user_id=user.id, category_id=categories[category].id, amount=amount, date=entry_date, description=description, payment_method=payment))
        db.session.add(SavingsGoal(user_id=user.id, name="Emergency fund", target_amount=300000, current_amount=112000, deadline=date(2027, 6, 30)))
        db.session.add(SavingsGoal(user_id=user.id, name="Family trip", target_amount=120000, current_amount=38000, deadline=date(2027, 3, 31)))
        db.session.commit()
    for month in ("2026-07", "2026-08", "2026-09"):
        plan = generate_rule_based_budget(user, month)
        save_budget_plan(user, month, plan["allocations"], source="seed")
    print("Seed complete")
    print("Demo login: demo@financebot.local / Demo@12345")
