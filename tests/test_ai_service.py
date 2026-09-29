def test_safe_json_and_rule_fallback(app):
    from app.services.ai_service import generate_recommendation, safe_parse_json
    from app.models import User
    assert safe_parse_json("```json\n{\"hello\": \"world\"}\n```")["hello"] == "world"
    with app.app_context():
        user = User.query.filter_by(email="alice@example.com").first()
        payload, record = generate_recommendation(user, "2026-09")
        assert record.provider == "rules"
        assert record.status == "fallback"
        assert payload["health_score"] >= 0
        assert "actions" in payload


def test_mocked_gemini_and_openai_adapters(app, monkeypatch):
    from app.services import ai_service

    class FakeResponse:
        def __init__(self, payload):
            self.payload = payload
        def raise_for_status(self):
            return None
        def json(self):
            return self.payload

    def fake_post(url, **kwargs):
        if "generativelanguage" in url:
            return FakeResponse({"candidates": [{"content": {"parts": [{"text": "{\"headline\":\"Gemini\"}"}]}}]})
        return FakeResponse({"choices": [{"message": {"content": "{\"headline\":\"OpenAI\"}"}}]})

    monkeypatch.setattr(ai_service.requests, "post", fake_post)
    with app.app_context():
        app.config.update(AI_PROVIDER="gemini", GEMINI_API_KEY="test-key")
        text, provider = ai_service.call_provider("return JSON")
        assert provider == "gemini" and "Gemini" in text
        app.config.update(AI_PROVIDER="openai", OPENAI_API_KEY="test-key")
        text, provider = ai_service.call_provider("return JSON")
        assert provider == "openai" and "OpenAI" in text


def test_malformed_provider_response_and_request_failure_fallback(app, monkeypatch):
    from app.models import User
    from app.services import ai_service
    with app.app_context():
        user = User.query.filter_by(email="alice@example.com").first()
        app.config.update(AI_PROVIDER="openai", OPENAI_API_KEY="test-key")
        monkeypatch.setattr(ai_service, "call_provider", lambda prompt: ("not-json", "openai"))
        payload, record = ai_service.generate_recommendation(user, "2026-09", kind="malformed")
        assert record.status == "fallback" and record.provider == "rules"
        def failing_provider(prompt):
            raise RuntimeError("provider unavailable")
        monkeypatch.setattr(ai_service, "call_provider", failing_provider)
        payload, record = ai_service.generate_recommendation(user, "2026-10", kind="failure")
        assert record.status == "fallback" and "actions" in payload
