from datetime import date
from pathlib import Path

from flask import Flask, jsonify, render_template, request
from flask_login import current_user

from config import Config
from .extensions import csrf, db, login_manager


def create_app(config_object=None):
    app = Flask(__name__, instance_relative_config=True)
    if isinstance(config_object, dict):
        app.config.from_object(Config)
        app.config.from_mapping(config_object)
    else:
        app.config.from_object(config_object or Config)
    Path(app.instance_path).mkdir(parents=True, exist_ok=True)

    db.init_app(app)
    login_manager.init_app(app)
    csrf.init_app(app)

    from .models import User

    @login_manager.user_loader
    def load_user(user_id):
        return db.session.get(User, int(user_id))

    from .auth.routes import auth_bp
    from .dashboard.routes import dashboard_bp
    from .income.routes import income_bp
    from .expenses.routes import expenses_bp
    from .budget.routes import budget_bp
    from .ai.routes import ai_bp
    from .reports.routes import reports_bp
    from .goals.routes import goals_bp
    from .profile.routes import profile_bp

    for blueprint in (auth_bp, dashboard_bp, income_bp, expenses_bp, budget_bp, ai_bp, reports_bp, goals_bp, profile_bp):
        app.register_blueprint(blueprint)

    @app.context_processor
    def inject_globals():
        return {
            "app_name": app.config["APP_NAME"],
            "today": date.today(),
            "current_user": current_user,
            "currency_symbol": getattr(current_user, "currency_symbol", "₹") if current_user.is_authenticated else "₹",
        }

    @app.after_request
    def add_security_headers(response):
        response.headers.setdefault("X-Content-Type-Options", "nosniff")
        response.headers.setdefault("Referrer-Policy", "strict-origin-when-cross-origin")
        if current_user.is_authenticated:
            response.headers["Cache-Control"] = "private, no-store"
        return response

    @app.get("/health")
    def health():
        return jsonify({"status": "ok", "service": "financebot"})

    @app.get("/manus-routes.json")
    def route_manifest():
        return app.send_static_file("manus-routes.json")

    @app.errorhandler(404)
    def not_found(error):
        if request.path.startswith("/api/"):
            return jsonify({"error": "Not found"}), 404
        return render_template("errors/404.html"), 404

    @app.errorhandler(500)
    def server_error(error):
        db.session.rollback()
        return render_template("errors/500.html"), 500

    with app.app_context():
        db.create_all()

    return app
