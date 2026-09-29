from flask import Blueprint, flash, redirect, render_template, url_for
from flask_login import current_user, login_required

from ..services.ai_service import generate_recommendation, latest_recommendation
from ..services.analytics import summary_for_user
from ..utils import selected_month

ai_bp = Blueprint("ai", __name__, url_prefix="/ai-advisor")


@ai_bp.get("")
@login_required
def index():
    month = selected_month()
    summary = summary_for_user(current_user, month)
    recommendation = latest_recommendation(current_user, month)
    return render_template("ai/index.html", month=month, summary=summary, recommendation=recommendation)


@ai_bp.post("/generate")
@login_required
def generate():
    month = selected_month()
    generate_recommendation(current_user, month)
    flash("Your advisor refreshed the plan. Review the suggestions below.", "success")
    return redirect(url_for("ai.index", month=month))
