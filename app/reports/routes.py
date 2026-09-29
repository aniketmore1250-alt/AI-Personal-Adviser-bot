from flask import Blueprint, flash, make_response, redirect, render_template, url_for
from flask_login import current_user, login_required

from ..services.report_service import csv_bytes, pdf_bytes, save_report
from ..utils import selected_month

reports_bp = Blueprint("reports", __name__, url_prefix="/reports")


@reports_bp.get("")
@login_required
def index():
    month = selected_month()
    payload, _ = save_report(current_user, month)
    return render_template("reports/index.html", month=month, report=payload)


@reports_bp.get("/<month>")
@login_required
def detail(month):
    from ..forms import parse_month
    try:
        month = parse_month(month)
    except ValueError:
        flash("Choose a valid month.", "error")
        return redirect(url_for("reports.index"))
    payload, _ = save_report(current_user, month)
    return render_template("reports/detail.html", month=month, report=payload)


@reports_bp.get("/<month>/csv")
@login_required
def csv_export(month):
    from ..forms import parse_month
    try:
        month = parse_month(month)
    except ValueError:
        return redirect(url_for("reports.index"))
    payload, _ = save_report(current_user, month)
    response = make_response(csv_bytes(payload))
    response.headers["Content-Type"] = "text/csv; charset=utf-8"
    response.headers["Content-Disposition"] = f"attachment; filename=finance-report-{month}.csv"
    return response


@reports_bp.get("/<month>/pdf")
@login_required
def pdf_export(month):
    from ..forms import parse_month
    try:
        month = parse_month(month)
    except ValueError:
        return redirect(url_for("reports.index"))
    payload, _ = save_report(current_user, month)
    response = make_response(pdf_bytes(payload))
    response.headers["Content-Type"] = "application/pdf"
    response.headers["Content-Disposition"] = f"attachment; filename=finance-report-{month}.pdf"
    return response
