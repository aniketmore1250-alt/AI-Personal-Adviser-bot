import json
import re

import requests
from flask import current_app

from ..extensions import db
from ..models import AIRecommendation
from .analytics import summary_for_user
from .budget_engine import generate_rule_based_budget


def safe_parse_json(value):
    if isinstance(value, dict):
        return value
    text = str(value or "").strip()
    text = re.sub(r"^```(?:json)?\s*|\s*```$", "", text, flags=re.IGNORECASE | re.DOTALL).strip()
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        match = re.search(r"\{.*\}", text, flags=re.DOTALL)
        if match:
            try:
                return json.loads(match.group(0))
            except json.JSONDecodeError:
                pass
    raise ValueError("AI response was not valid JSON")


def fallback_payload(user, month, reason="No provider key configured"):
    summary = summary_for_user(user, month)
    budget = generate_rule_based_budget(user, month)
    overspending = [item["category"] for item in summary["overspent_categories"]]
    savings_action = "Keep a weekly savings transfer" if summary["savings_rate"] < 20 else "Protect your savings habit and automate it"
    user_type_copy = {
        "student": "Prioritize essentials, use a weekly allowance, and keep discretionary spending visible.",
        "freelancer": "Keep a larger cash buffer for uneven client income and set aside taxes before lifestyle spending.",
        "household": "Review groceries, utilities, and healthcare together so family priorities stay funded.",
        "salaried": "Automate savings on payday and give flexible spending a clear monthly ceiling.",
    }.get((user.user_type or "salaried").lower(), "Make one small, repeatable improvement this month.")
    return {
        "headline": "A practical plan for this month",
        "summary": "This guidance uses your tracked activity and simple budgeting rules. It is a useful starting point, not professional financial advice.",
        "health_score": summary["health_score"],
        "health_explanation": summary["health_explanation"],
        "insights": [
            f"Your net savings this month are {summary['net_savings']:.2f} with a savings rate of {summary['savings_rate']:.1f}%.",
            f"{overspending[0]} is the first category to review." if overspending else "No budget category is currently over its limit.",
            user_type_copy,
        ],
        "actions": [
            savings_action,
            "Review your top spending category once a week.",
            "Build toward 3–6 months of essential expenses for an emergency fund.",
        ],
        "emergency_fund": summary["emergency_fund"],
        "budget": budget,
        "overspending": overspending,
        "source_note": reason,
    }


def prompt_for(user, month):
    summary = summary_for_user(user, month)
    return f"""You are a supportive financial planning assistant. Return JSON only with keys headline, summary, health_score, health_explanation, insights (array), actions (array), emergency_fund (object), budget (object), and overspending (array). Do not provide regulated investment, lending, tax, or legal advice. User type: {user.user_type}. Goals: {user.financial_goals}. Monthly income profile: {float(user.monthly_income or 0)}. Month: {month}. Data: {json.dumps(summary)}. Apply a practical 50/30/20-informed budget adjusted to the user's actual categories and goals. Keep the tone friendly and non-judgmental."""


def call_provider(prompt):
    provider = current_app.config.get("AI_PROVIDER", "rules")
    if provider == "gemini" and current_app.config.get("GEMINI_API_KEY"):
        url = "https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent"
        response = requests.post(f"{url}?key={current_app.config['GEMINI_API_KEY']}", json={"contents": [{"parts": [{"text": prompt}]}]}, timeout=20)
        response.raise_for_status()
        data = response.json()
        return data["candidates"][0]["content"]["parts"][0]["text"], "gemini"
    if provider == "openai" and current_app.config.get("OPENAI_API_KEY"):
        response = requests.post(
            "https://api.openai.com/v1/chat/completions",
            headers={"Authorization": f"Bearer {current_app.config['OPENAI_API_KEY']}"},
            json={"model": "gpt-4o-mini", "temperature": 0.3, "messages": [{"role": "system", "content": "Return valid JSON only."}, {"role": "user", "content": prompt}]},
            timeout=20,
        )
        response.raise_for_status()
        return response.json()["choices"][0]["message"]["content"], "openai"
    raise RuntimeError("No AI provider key configured")


def normalize(payload):
    payload = dict(payload or {})
    payload.setdefault("headline", "Your personal finance check-in")
    payload.setdefault("summary", "Review the suggestions below at your own pace.")
    payload["health_score"] = max(0, min(100, int(payload.get("health_score", 50))))
    payload.setdefault("health_explanation", "Your score is an informational snapshot based on your tracked activity.")
    payload["insights"] = list(payload.get("insights") or [])[:6]
    payload["actions"] = list(payload.get("actions") or [])[:6]
    payload.setdefault("emergency_fund", {})
    payload.setdefault("budget", {})
    payload.setdefault("overspending", [])
    return payload


def generate_recommendation(user, month, kind="advisor"):
    provider = current_app.config.get("AI_PROVIDER", "rules")
    status = "fallback"
    reason = "Rule-based guidance is active because no AI provider is configured."
    try:
        raw, used_provider = call_provider(prompt_for(user, month))
        payload = normalize(safe_parse_json(raw))
        provider = used_provider
        status = "success"
        reason = "Generated with the selected AI provider."
    except Exception as error:
        payload = normalize(fallback_payload(user, month, str(error)))
        provider = "rules"
    payload["source_note"] = payload.get("source_note", reason)
    recommendation = AIRecommendation(user_id=user.id, kind=kind, month=month, payload_json=json.dumps(payload), provider=provider, status=status)
    db.session.add(recommendation)
    db.session.commit()
    return payload, recommendation


def latest_recommendation(user, month):
    recommendation = AIRecommendation.query.filter_by(user_id=user.id, month=month).order_by(AIRecommendation.created_at.desc()).first()
    if not recommendation:
        return fallback_payload(user, month)
    try:
        return normalize(json.loads(recommendation.payload_json))
    except (ValueError, TypeError, json.JSONDecodeError):
        return fallback_payload(user, month, "Stored recommendation could not be read")
