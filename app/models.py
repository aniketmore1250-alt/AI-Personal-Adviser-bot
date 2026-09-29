from datetime import datetime
from decimal import Decimal

from flask_login import UserMixin
from werkzeug.security import check_password_hash, generate_password_hash

from .extensions import db


DEFAULT_CATEGORIES = [
    "Rent", "Food", "Transport", "Utilities", "Groceries", "Education",
    "Healthcare", "Entertainment", "Shopping", "Savings", "Other",
]


class User(UserMixin, db.Model):
    __tablename__ = "users"
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), nullable=False)
    email = db.Column(db.String(255), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(255), nullable=False)
    monthly_income = db.Column(db.Numeric(12, 2), default=0, nullable=False)
    currency = db.Column(db.String(8), default="INR", nullable=False)
    financial_goals = db.Column(db.Text, default="", nullable=False)
    savings_target = db.Column(db.Numeric(12, 2), default=0, nullable=False)
    user_type = db.Column(db.String(40), default="salaried", nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)

    incomes = db.relationship("Income", back_populates="user", cascade="all, delete-orphan")
    expenses = db.relationship("Expense", back_populates="user", cascade="all, delete-orphan")
    categories = db.relationship("ExpenseCategory", back_populates="user", cascade="all, delete-orphan")
    budgets = db.relationship("Budget", back_populates="user", cascade="all, delete-orphan")
    savings_goals = db.relationship("SavingsGoal", back_populates="user", cascade="all, delete-orphan")
    monthly_reports = db.relationship("MonthlyReport", back_populates="user", cascade="all, delete-orphan")
    ai_recommendations = db.relationship("AIRecommendation", back_populates="user", cascade="all, delete-orphan")

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    @property
    def currency_symbol(self):
        return {"INR": "₹", "USD": "$", "EUR": "€", "GBP": "£"}.get(self.currency, self.currency)


class Income(db.Model):
    __tablename__ = "incomes"
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    source_name = db.Column(db.String(120), nullable=False)
    amount = db.Column(db.Numeric(12, 2), nullable=False)
    date = db.Column(db.Date, nullable=False, index=True)
    notes = db.Column(db.String(500), default="", nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    user = db.relationship("User", back_populates="incomes")


class ExpenseCategory(db.Model):
    __tablename__ = "expense_categories"
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    name = db.Column(db.String(80), nullable=False)
    is_default = db.Column(db.Boolean, default=False, nullable=False)
    is_active = db.Column(db.Boolean, default=True, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    user = db.relationship("User", back_populates="categories")
    expenses = db.relationship("Expense", back_populates="category")
    budgets = db.relationship("Budget", back_populates="category")
    __table_args__ = (db.UniqueConstraint("user_id", "name", name="uq_user_category_name"),)


class Expense(db.Model):
    __tablename__ = "expenses"
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    category_id = db.Column(db.Integer, db.ForeignKey("expense_categories.id"), nullable=False, index=True)
    amount = db.Column(db.Numeric(12, 2), nullable=False)
    date = db.Column(db.Date, nullable=False, index=True)
    description = db.Column(db.String(240), default="", nullable=False)
    payment_method = db.Column(db.String(40), default="UPI", nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    user = db.relationship("User", back_populates="expenses")
    category = db.relationship("ExpenseCategory", back_populates="expenses")


class Budget(db.Model):
    __tablename__ = "budgets"
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    category_id = db.Column(db.Integer, db.ForeignKey("expense_categories.id"), nullable=False, index=True)
    month = db.Column(db.String(7), nullable=False, index=True)
    limit_amount = db.Column(db.Numeric(12, 2), nullable=False)
    source = db.Column(db.String(20), default="manual", nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    user = db.relationship("User", back_populates="budgets")
    category = db.relationship("ExpenseCategory", back_populates="budgets")
    __table_args__ = (db.UniqueConstraint("user_id", "category_id", "month", name="uq_user_budget_month_category"),)


class SavingsGoal(db.Model):
    __tablename__ = "savings_goals"
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    name = db.Column(db.String(120), nullable=False)
    target_amount = db.Column(db.Numeric(12, 2), nullable=False)
    current_amount = db.Column(db.Numeric(12, 2), default=0, nullable=False)
    deadline = db.Column(db.Date, nullable=True)
    status = db.Column(db.String(20), default="active", nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    user = db.relationship("User", back_populates="savings_goals")

    @property
    def progress_percent(self):
        target = float(self.target_amount or 0)
        return min(100, round(float(self.current_amount or 0) / target * 100, 1)) if target else 0


class MonthlyReport(db.Model):
    __tablename__ = "monthly_reports"
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    month = db.Column(db.String(7), nullable=False, index=True)
    summary_json = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    user = db.relationship("User", back_populates="monthly_reports")
    __table_args__ = (db.UniqueConstraint("user_id", "month", name="uq_user_report_month"),)


class AIRecommendation(db.Model):
    __tablename__ = "ai_recommendations"
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    kind = db.Column(db.String(40), default="advisor", nullable=False)
    month = db.Column(db.String(7), nullable=False, index=True)
    payload_json = db.Column(db.Text, nullable=False)
    provider = db.Column(db.String(30), default="rules", nullable=False)
    status = db.Column(db.String(30), default="success", nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    user = db.relationship("User", back_populates="ai_recommendations")
