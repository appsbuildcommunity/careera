import json
import os
from typing import Any, Optional

from langchain_core.language_models.chat_models import BaseChatModel
from langchain_core.messages import HumanMessage, SystemMessage
from pydantic import BaseModel, SecretStr

from app.share.service.llm.exceptions import LLMProviderError
from app.share.service.llm.mock import MockChatModel

__all__ = ["LLMProviderError", "get_llm_provider", "generate_json"]

SUPPORTED_PROVIDERS: tuple[str, ...] = (
    "mock",
    "gemini",
    "openai",
    "anthropic",
    "deepseek",
)

_MODEL_DEFAULTS: dict[str, str] = {
    "gemini": "gemini-1.5-flash",
    "openai": "gpt-4o-mini",
    "anthropic": "claude-sonnet-4-20250514",
    "deepseek": "deepseek-chat",
}

_DEEPSEEK_DEFAULT_URL = "https://api.deepseek.com"


def get_llm_provider() -> BaseChatModel:
    """Return the LangChain chat model selected via environment variables."""
    provider_name = os.getenv("LLM_PROVIDER", "mock").lower()
    api_key = os.getenv("LLM_API_KEY", "")
    model_name = os.getenv("LLM_MODEL", "")
    llm_url = os.getenv("LLM_URL", "")

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
            base_url=llm_url or None,
        )

    if provider_name == "deepseek":
        from langchain_openai import ChatOpenAI

        return ChatOpenAI(
            model=model_name or _MODEL_DEFAULTS["deepseek"],
            api_key=SecretStr(api_key),
            base_url=llm_url or _DEEPSEEK_DEFAULT_URL,
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


def _dump_result(result: Any) -> dict[str, Any]:
    if isinstance(result, BaseModel):
        return result.model_dump()
    return dict(result)


def _structured_runnable(
    model: BaseChatModel,
    system: str,
    response_model: type[BaseModel],
) -> tuple[Any, str]:
    """Return ``(structured_output_runnable, system_prompt)`` for the model.

    OpenAI-compatible models (``openai`` / ``deepseek``) default to the
    ``json_schema`` response_format, which DeepSeek's reasoning models reject.
    They also reject ``function_calling`` (tool calling). The supported path is
    ``json_mode`` with the JSON schema embedded in the system prompt. Gemini /
    Anthropic / mock use their native ``with_structured_output``.
    """
    try:
        from langchain_openai import ChatOpenAI
    except ImportError:
        return model.with_structured_output(response_model), system
    if isinstance(model, ChatOpenAI):
        schema = json.dumps(response_model.model_json_schema())
        augmented = (
            f"{system}\n\nReturn ONLY valid JSON matching the following JSON "
            f"Schema, with no additional fields:\n{schema}"
        )
        return (
            model.with_structured_output(response_model, method="json_mode"),
            augmented,
        )
    return model.with_structured_output(response_model), system


async def generate_json(
    *,
    model: Optional[BaseChatModel] = None,
    system: str,
    user: str,
    response_model: type[BaseModel],
) -> dict[str, Any]:
    """Generate a validated JSON object using a LangChain chat model.

    If ``model`` is omitted it is created via ``get_llm_provider()``.
    Runs ``with_structured_output(response_model)`` and returns the result
    validated against the Pydantic class as a dict. Uses ``ainvoke`` so real
    providers (gemini / openai / anthropic / deepseek) perform the network call
    through their native async path and the event loop is never blocked. The
    mock provider falls back to LangChain's default async wrapper, which is
    cheap.
    """
    if model is None:
        model = get_llm_provider()
    structured, system_prompt = _structured_runnable(model, system, response_model)
    messages = [
        SystemMessage(content=system_prompt),
        HumanMessage(content=user),
    ]
    try:
        result = await structured.ainvoke(messages)
        return _dump_result(result)
    except Exception as exc:
        raise LLMProviderError(f"LLM call failed: {exc}") from exc
