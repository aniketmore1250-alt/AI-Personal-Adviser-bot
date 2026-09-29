from flask import abort, request

from .extensions import db
from .forms import current_month, parse_month
from .models import DEFAULT_CATEGORIES, ExpenseCategory


def ensure_default_categories(user):
    existing = {item.name for item in user.categories}
    for name in DEFAULT_CATEGORIES:
        if name not in existing:
            db.session.add(ExpenseCategory(user_id=user.id, name=name, is_default=True))
    db.session.commit()


def selected_month():
    value = request.args.get("month") or request.form.get("month") or current_month()
    try:
        return parse_month(value)
    except ValueError:
        return current_month()


def owned_or_404(model, record_id, user_id):
    item = model.query.filter_by(id=record_id, user_id=user_id).first()
    if not item:
        abort(404)
    return item
