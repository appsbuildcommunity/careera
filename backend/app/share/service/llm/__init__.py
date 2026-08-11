import os
from typing import Any, Optional

from langchain_core.language_models.chat_models import BaseChatModel
from langchain_core.messages import HumanMessage, SystemMessage
from pydantic import BaseModel, SecretStr

from app.share.service.llm.exceptions import LLMProviderError
from app.share.service.llm.mock import MockChatModel

__all__ = ["LLMProviderError", "get_llm_provider", "generate_json"]

SUPPORTED_PROVIDERS: tuple[str, ...] = ("mock", "gemini", "openai", "anthropic")

_MODEL_DEFAULTS: dict[str, str] = {
    "gemini": "gemini-1.5-flash",
    "openai": "gpt-4o-mini",
    "anthropic": "claude-sonnet-4-20250514",
}


def get_llm_provider() -> BaseChatModel:
    """Return the LangChain chat model selected via environment variables."""
    provider_name = os.getenv("LLM_PROVIDER", "mock").lower()
    api_key = os.getenv("LLM_API_KEY", "")
    model_name = os.getenv("LLM_MODEL", "")

    if provider_name == "mock":
        return MockChatModel()

    if not api_key:
        raise LLMProviderError(
            f"LLM_API_KEY is not configured for provider '{provider_name}'."
        )

    if provider_name == "gemini":
        from langchain_google_genai import ChatGoogleGenerativeAI

        return ChatGoogleGenerativeAI(
            model=model_name or _MODEL_DEFAULTS["gemini"],
            google_api_key=SecretStr(api_key),
        )

    if provider_name == "openai":
        from langchain_openai import ChatOpenAI

        return ChatOpenAI(
            model=model_name or _MODEL_DEFAULTS["openai"],
            api_key=SecretStr(api_key),
        )

    if provider_name == "anthropic":
        from langchain_anthropic import ChatAnthropic

        return ChatAnthropic(
            model_name=model_name or _MODEL_DEFAULTS["anthropic"],
            api_key=SecretStr(api_key),
            max_tokens_to_sample=4096,
            timeout=None,
            stop=None,
        )

    raise LLMProviderError(
        f"Unknown LLM_PROVIDER '{provider_name}'. "
        f"Supported providers: {list(SUPPORTED_PROVIDERS)}."
    )


def generate_json(
    *,
    model: Optional[BaseChatModel] = None,
    system: str,
    user: str,
    response_model: type[BaseModel],
) -> dict[str, Any]:
    """Generate a validated JSON object using a LangChain chat model.

    If ``model`` is omitted it is created via ``get_llm_provider()``.
    Runs ``with_structured_output(response_model)`` — the provider's native
    tool-calling path — and returns the result validated against the Pydantic
    class as a dict.
    """
    if model is None:
        model = get_llm_provider()
    messages = [SystemMessage(content=system), HumanMessage(content=user)]
    try:
        result = model.with_structured_output(response_model).invoke(messages)
        if isinstance(result, BaseModel):
            return result.model_dump()
        return dict(result)
    except Exception as exc:
        raise LLMProviderError(f"LLM call failed: {exc}") from exc
