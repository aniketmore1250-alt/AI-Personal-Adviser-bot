# Personal Finance Advisor Bot

Personal Finance Advisor Bot is a Flask-based personal finance workspace for tracking income and expenses, planning category budgets, following savings goals, and generating supportive financial guidance. It uses server-rendered Jinja2 pages, SQLAlchemy, Flask-Login, CSRF-protected forms, Chart.js, SQLite by default, and optional Gemini or OpenAI provider calls. If no provider key is configured, the rule-based advisor remains fully usable.

> **Disclaimer:** AI suggestions are informational and are not professional financial, investment, tax, legal, or lending advice.

## Stack

- Python Flask 3 with Blueprints, SQLAlchemy ORM, Flask-Login, Flask-WTF/CSRF, and python-dotenv
- SQLite by default; set `DATABASE_URL` to a PostgreSQL SQLAlchemy URL when needed
- Jinja2 templates, CSS3, JavaScript, and Chart.js
- Optional Google Gemini or OpenAI API calls with defensive JSON parsing and rule-based fallback
- ReportLab PDF export and CSV export
- Optional Ngrok tunnel through pyngrok or the standard CLI

## Local setup

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
python seed.py
python run.py
```

Open `http://127.0.0.1:3000`. `run.py` binds to `0.0.0.0` and reads `PORT`; the managed Webdev preview uses the same port contract. For local HTTP, keep `SESSION_COOKIE_SAMESITE=Lax` and `SESSION_COOKIE_SECURE=false`.

### Demo account

- Email: `demo@financebot.local`
- Password: `Demo@12345`

The seed script is deterministic and creates three months of sample income, expenses, budgets, and savings goals. It is for development/demo use only.

## Environment variables

Copy `.env.example` to `.env` and change at least `SECRET_KEY`. The default `DATABASE_URL` points to `instance/financebot.db`. For PostgreSQL, use a URL such as `postgresql+psycopg2://user:password@host:5432/financebot`.

Set `AI_PROVIDER=gemini` with `GEMINI_API_KEY`, or `AI_PROVIDER=openai` with `OPENAI_API_KEY`, to enable provider calls. Leave `AI_PROVIDER=rules` for a no-key local setup. Provider keys are server-side only and are never rendered into browser JavaScript.

Cloud Preview is served inside a cross-site HTTPS iframe. Start the Preview process with `SESSION_COOKIE_SAMESITE=None` and `SESSION_COOKIE_SECURE=true` so the Flask session cookie reaches registration/login POSTs and CSRF remains valid. Do not disable CSRF or exempt auth routes. If you run the app directly over local HTTP, switch back to `Lax` and `false` because browsers do not send `Secure` cookies over plain HTTP.

## Ngrok access

### CLI (recommended for local work)

With the app running on port 3000:

```bash
ngrok config add-authtoken YOUR_TOKEN
ngrok http 3000
```

Copy the HTTPS forwarding URL from the Ngrok terminal. Do not commit the token.

### pyngrok through `run.py`

Set `NGROK_AUTHTOKEN=...` and `ENABLE_NGROK=true` in `.env`, then run `python run.py`. The process prints the public URL. If the token or binary is unavailable, the app still starts locally and prints a friendly warning.

## Tests and checks

```bash
source .venv/bin/activate
python -m compileall app run.py seed.py
pytest
```

Tests cover authentication and data isolation, income and expense CRUD, budget generation, mocked AI provider/fallback behavior, dashboard summaries, and report exports.

## Deployment

The included `Dockerfile` installs the pinned dependencies and runs Gunicorn on `$PORT`. The unauthenticated `/health` endpoint returns JSON for deployment health checks. The app serves SSR HTML, static assets, CSV/PDF exports, and all protected routes from one origin; authenticated responses are marked private/no-store. Durable application data should use the configured database rather than container-local filesystem state. Managed MySQL URLs with JSON `ssl` query parameters are normalized into PyMySQL SSL options at startup, so the container does not pass a string where the driver expects a mapping.

For a managed Webdev project, declare the server/container deployment with `healthPath: /health` and use the project's runtime port. Preview is not the same as a permanent published deployment; only share a permanent URL after a confirmed publish result.

## Project map

- `app/models.py` contains User, Income, ExpenseCategory, Expense, Budget, SavingsGoal, MonthlyReport, and AIRecommendation.
- `app/services/analytics.py` computes monthly summaries, health scores, emergency-fund progress, category analytics, and trends.
- `app/services/budget_engine.py` provides the user-type-aware 50/30/20 starting plan and persists manual/AI limits.
- `app/services/ai_service.py` handles provider selection, structured JSON prompts, fallback logic, and stored recommendations.
- `app/services/report_service.py` generates persisted month reports plus CSV/PDF bytes.
- Blueprints in `app/*/routes.py` keep auth, dashboard, income, expenses, budget, AI, reports, goals, and profile flows separated.

The service boundaries are intentionally future-ready for predictive spending analytics, investment suggestions, goal-based savings automation, and deeper financial health monitoring without changing the core route contracts.
