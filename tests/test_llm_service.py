import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from services import llm_service
from utils.token_counter import estimate_cost


def test_get_llm_uses_configured_gemini_model(monkeypatch):
    created = {}

    def fake_chat_gemini(**kwargs):
        created.update(kwargs)
        return object()

    monkeypatch.setattr(llm_service, "ChatGoogleGenerativeAI", fake_chat_gemini)
    monkeypatch.setattr(llm_service.Config, "GEMINI_MODEL", "gemini-3.5-flash-lite")
    monkeypatch.setattr(llm_service.Config, "GOOGLE_API_KEY", "test-api-key")
    monkeypatch.setattr(llm_service, "_llm_instance", None)

    llm_service.get_llm()

    assert created["model"] == "gemini-3.5-flash-lite"
    assert created["google_api_key"] == "test-api-key"
    assert created["temperature"] == 0.2


def test_free_tier_model_cost_estimate_is_zero():
    assert estimate_cost(100_000, 20_000) == 0.0


def test_get_llm_requires_api_key(monkeypatch):
    monkeypatch.setattr(llm_service.Config, "GOOGLE_API_KEY", "")
    monkeypatch.setattr(llm_service, "_llm_instance", None)

    try:
        llm_service.get_llm()
    except RuntimeError as error:
        assert "GOOGLE_API_KEY is missing" in str(error)
    else:
        raise AssertionError("Expected missing API key to be reported")
