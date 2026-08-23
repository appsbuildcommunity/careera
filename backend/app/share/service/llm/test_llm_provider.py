import pytest
from typing import Any, cast

from app.share.service.llm import LLMProviderError, get_llm_provider
from app.share.service.llm.mock import MockChatModel


@pytest.fixture(autouse=True)
def clear_llm_env(monkeypatch):
    monkeypatch.delenv("LLM_PROVIDER", raising=False)
    monkeypatch.delenv("LLM_API_KEY", raising=False)
    monkeypatch.delenv("LLM_MODEL", raising=False)
    monkeypatch.delenv("LLM_URL", raising=False)


def test_default_provider_is_mock():
    assert isinstance(get_llm_provider(), MockChatModel)


def test_provider_name_is_case_insensitive(monkeypatch):
    monkeypatch.setenv("LLM_PROVIDER", "MOCK")
    assert isinstance(get_llm_provider(), MockChatModel)


@pytest.mark.parametrize(
    ("provider_name", "expected_class"),
    [
        ("gemini", "ChatGoogleGenerativeAI"),
        ("openai", "ChatOpenAI"),
        ("anthropic", "ChatAnthropic"),
        ("deepseek", "ChatOpenAI"),
    ],
)
def test_real_providers_build_with_key(monkeypatch, provider_name, expected_class):
    monkeypatch.setenv("LLM_PROVIDER", provider_name)
    monkeypatch.setenv("LLM_API_KEY", "dummy-key")
    assert type(get_llm_provider()).__name__ == expected_class


@pytest.mark.parametrize(
    "provider_name", ["gemini", "openai", "anthropic", "deepseek"]
)
def test_real_provider_requires_api_key(monkeypatch, provider_name):
    monkeypatch.setenv("LLM_PROVIDER", provider_name)
    with pytest.raises(LLMProviderError, match="LLM_API_KEY is not configured"):
        get_llm_provider()


def test_unknown_provider_raises(monkeypatch):
    monkeypatch.setenv("LLM_PROVIDER", "azure")
    with pytest.raises(LLMProviderError, match="azure"):
        get_llm_provider()


@pytest.mark.parametrize(
    "provider_name", ["gemini", "openai", "anthropic", "deepseek"]
)
def test_model_override(monkeypatch, provider_name):
    monkeypatch.setenv("LLM_PROVIDER", provider_name)
    monkeypatch.setenv("LLM_API_KEY", "dummy-key")
    monkeypatch.setenv("LLM_MODEL", "custom-model-x")
    assert cast(Any, get_llm_provider()).model == "custom-model-x"


def test_default_models_when_model_unset(monkeypatch):
    defaults = {
        "gemini": "gemini-3.6-flash",
        "openai": "gpt-4o-mini",
        "anthropic": "claude-sonnet-4-20250514",
        "deepseek": "deepseek-chat",
    }
    monkeypatch.setenv("LLM_API_KEY", "dummy-key")
    for provider_name, default_model in defaults.items():
        monkeypatch.setenv("LLM_PROVIDER", provider_name)
        assert cast(Any, get_llm_provider()).model == default_model


def test_deepseek_defaults_to_deepseek_base_url(monkeypatch):
    monkeypatch.setenv("LLM_PROVIDER", "deepseek")
    monkeypatch.setenv("LLM_API_KEY", "dummy-key")
    assert (
        cast(Any, get_llm_provider()).openai_api_base
        == "https://api.deepseek.com"
    )


def test_deepseek_uses_llm_url_override(monkeypatch):
    monkeypatch.setenv("LLM_PROVIDER", "deepseek")
    monkeypatch.setenv("LLM_API_KEY", "dummy-key")
    monkeypatch.setenv("LLM_URL", "https://custom-proxy.example.com")
    assert (
        cast(Any, get_llm_provider()).openai_api_base
        == "https://custom-proxy.example.com"
    )
