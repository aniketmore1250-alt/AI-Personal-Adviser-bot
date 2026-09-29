import csv
import io
import json
from datetime import datetime

from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas

from ..extensions import db
from ..models import MonthlyReport
from .ai_service import latest_recommendation
from .analytics import summary_for_user


def build_report(user, month):
    summary = summary_for_user(user, month)
    recommendation = latest_recommendation(user, month)
    return {
        "month": month,
        "summary": summary,
        "recommendation": recommendation,
        "next_month_goals": [
            "Keep essential categories within their limit.",
            "Move one automatic transfer toward your emergency fund.",
            "Review the top spending category before the next month begins.",
        ],
        "generated_at": datetime.utcnow().isoformat(),
    }


def save_report(user, month):
    payload = build_report(user, month)
    report = MonthlyReport.query.filter_by(user_id=user.id, month=month).first()
    if not report:
        report = MonthlyReport(user_id=user.id, month=month)
        db.session.add(report)
    report.summary_json = json.dumps(payload)
    db.session.commit()
    return payload, report


def csv_bytes(payload):
    output = io.StringIO()
    writer = csv.writer(output)
    summary = payload["summary"]
    writer.writerow(["Personal Finance Advisor Bot", payload["month"]])
    writer.writerow(["Metric", "Amount"])
    writer.writerow(["Income", summary["income_total"]])
    writer.writerow(["Expenses", summary["expense_total"]])
    writer.writerow(["Net savings", summary["net_savings"]])
    writer.writerow(["Savings rate", summary["savings_rate"]])
    writer.writerow([])
    writer.writerow(["Category", "Actual", "Budget", "Status"])
    for item in summary["budget_performance"]:
        writer.writerow([item["category"], item["actual"], item["limit"], item["status"]])
    return output.getvalue().encode("utf-8")


def pdf_bytes(payload):
    buffer = io.BytesIO()
    pdf = canvas.Canvas(buffer, pagesize=letter)
    width, height = letter
    y = height - 48
    summary = payload["summary"]
    pdf.setTitle(f"Finance report {payload['month']}")
    pdf.setFont("Helvetica-Bold", 18)
    pdf.drawString(48, y, "Personal Finance Advisor Bot")
    y -= 26
    pdf.setFont("Helvetica", 11)
    pdf.drawString(48, y, f"Monthly report: {payload['month']}")
    y -= 28
    for label, value in (("Income", summary["income_total"]), ("Expenses", summary["expense_total"]), ("Net savings", summary["net_savings"]), ("Savings rate", f"{summary['savings_rate']}%"), ("Health score", summary["health_score"])):
        pdf.drawString(60, y, f"{label}: {value}")
        y -= 18
    y -= 8
    pdf.setFont("Helvetica-Bold", 12)
    pdf.drawString(48, y, "Category performance")
    y -= 20
    pdf.setFont("Helvetica", 10)
    for item in summary["budget_performance"]:
        pdf.drawString(60, y, f"{item['category']}: {item['actual']} / {item['limit']} ({item['status']})")
        y -= 15
        if y < 60:
            pdf.showPage()
            y = height - 48
            pdf.setFont("Helvetica", 10)
    y -= 8
    pdf.setFont("Helvetica-Oblique", 9)
    pdf.drawString(48, max(y, 40), "Informational guidance only; not professional financial advice.")
    pdf.save()
    return buffer.getvalue()
