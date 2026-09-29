from flask import Blueprint, render_template
from flask_login import current_user, login_required

from ..services.ai_service import latest_recommendation
from ..services.analytics import summary_for_user
from ..utils import ensure_default_categories, selected_month

dashboard_bp = Blueprint("dashboard", __name__, url_prefix="/dashboard")


@dashboard_bp.get("")
@login_required
def index():
    ensure_default_categories(current_user)
    month = selected_month()
    summary = summary_for_user(current_user, month)
    recommendation = latest_recommendation(current_user, month)
    return render_template("dashboard/index.html", month=month, summary=summary, recommendation=recommendation)
