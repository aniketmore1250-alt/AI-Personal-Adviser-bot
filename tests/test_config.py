from urllib.parse import quote


def test_mysql_ssl_query_is_normalized_to_pymysql_mapping(monkeypatch):
    from config import database_settings

    ssl_json = quote('{"rejectUnauthorized":true}')
    monkeypatch.setenv("DATABASE_URL", f"mysql://user:password@db.example/finance?ssl={ssl_json}&charset=utf8mb4")
    uri, engine_options = database_settings()

    assert uri.startswith("mysql+pymysql://")
    assert "ssl=" not in uri
    assert "charset=utf8mb4" in uri
    assert engine_options["connect_args"]["ssl"]["verify_mode"] == "required"
    assert "rejectUnauthorized" not in engine_options["connect_args"]["ssl"]


def test_sqlite_database_keeps_simple_engine_options(monkeypatch):
    from config import database_settings

    monkeypatch.setenv("DATABASE_URL", "sqlite:////tmp/financebot-config-test.db")
    uri, engine_options = database_settings()

    assert uri.startswith("sqlite:")
    assert "connect_args" not in engine_options
    assert engine_options["pool_pre_ping"] is True
