import os
import json
from pathlib import Path
from urllib.parse import parse_qsl, urlencode, urlsplit, urlunsplit
from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent
load_dotenv(BASE_DIR / ".env")


def env_bool(name, default=False):
    value = os.getenv(name)
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "on"}


def database_settings():
    uri = os.getenv("DATABASE_URL", f"sqlite:///{BASE_DIR / 'instance' / 'financebot.db'}")
    if uri.startswith("postgres://"):
        uri = uri.replace("postgres://", "postgresql://", 1)
    if not uri.startswith("mysql://"):
        return uri, {"pool_pre_ping": True}

    uri = uri.replace("mysql://", "mysql+pymysql://", 1)
    parsed = urlsplit(uri)
    query = parse_qsl(parsed.query, keep_blank_values=True)
    ssl_value = next((value for key, value in query if key == "ssl"), None)
    query = [(key, value) for key, value in query if key != "ssl"]
    engine_options = {"pool_pre_ping": True}
    if ssl_value:
        try:
            ssl_options = json.loads(ssl_value)
        except json.JSONDecodeError:
            ssl_options = {"ca": ssl_value}
        if not isinstance(ssl_options, dict):
            ssl_options = {}
        if "rejectUnauthorized" in ssl_options and "verify_mode" not in ssl_options:
            ssl_options["verify_mode"] = "required" if ssl_options.pop("rejectUnauthorized") else "none"
        engine_options["connect_args"] = {"ssl": ssl_options}
    return urlunsplit((parsed.scheme, parsed.netloc, parsed.path, urlencode(query), parsed.fragment)), engine_options


class Config:
    SECRET_KEY = os.getenv("SECRET_KEY", "dev-only-change-me")
    SQLALCHEMY_DATABASE_URI, SQLALCHEMY_ENGINE_OPTIONS = database_settings()
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    WTF_CSRF_TIME_LIMIT = None
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = os.getenv("SESSION_COOKIE_SAMESITE", "Lax")
    SESSION_COOKIE_SECURE = env_bool("SESSION_COOKIE_SECURE", os.getenv("FLASK_ENV") == "production")
    AI_PROVIDER = os.getenv("AI_PROVIDER", "gemini").lower()
    GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")
    OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
    NGROK_AUTHTOKEN = os.getenv("NGROK_AUTHTOKEN", "")
    ENABLE_NGROK = os.getenv("ENABLE_NGROK", "false").lower() == "true"
    PORT = int(os.getenv("PORT", "3000"))
    APP_NAME = "Personal Finance Advisor Bot"
    DEFAULT_CURRENCY = "INR"
