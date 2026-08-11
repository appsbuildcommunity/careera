import asyncio
from typing import Any

import pytest
from pydantic import BaseModel, Field

from app.share.service.llm import LLMProviderError, generate_json, get_llm_provider
from app.share.service.llm.mock import MockChatModel


class MovieInfo(BaseModel):
    name: str = Field(description="Movie name.")
    year: int = Field(description="Release year.")


class TitleOnly(BaseModel):
    title: str


@pytest.fixture(autouse=True)
def clear_llm_env(monkeypatch):
    monkeypatch.delenv("LLM_PROVIDER", raising=False)
    monkeypatch.delenv("LLM_API_KEY", raising=False)
    monkeypatch.delenv("LLM_MODEL", raising=False)
    monkeypatch.delenv("LLM_URL", raising=False)


def test_response_model_is_required():
    with pytest.raises(TypeError):
        asyncio.run(generate_json(system="s", user="u"))  # type: ignore[call-arg]


def test_model_is_keyword_only():
    with pytest.raises(TypeError):
        asyncio.run(
            generate_json(get_llm_provider(), system="s", user="u", response_model=TitleOnly)  # type: ignore[call-arg]
        )


def test_auto_instantiates_model_when_omitted():
    result = asyncio.run(
        generate_json(system="s", user="career path", response_model=TitleOnly)
    )
    assert isinstance(result, dict)
    assert "nodes" in result


def test_explicit_mock_model():
    result = asyncio.run(
        generate_json(
            model=MockChatModel(),
            system="s",
            user="interview template",
            response_model=TitleOnly,
        )
    )
    assert "questions" in result


def test_base_model_result_is_dumped():
    class _StubRunnable:
        async def ainvoke(self, messages):
            return MovieInfo(name="Inception", year=2010)

    class _StubModel:
        def with_structured_output(self, schema):
            assert schema is MovieInfo
            return _StubRunnable()

    result = asyncio.run(
        generate_json(
            model=_StubModel(), system="s", user="u", response_model=MovieInfo  # type: ignore[arg-type]
        )
    )
    assert result == {"name": "Inception", "year": 2010}


def test_dict_result_is_passed_through():
    class _StubRunnable:
        async def ainvoke(self, messages):
            return {"name": "Inception", "year": 2010}

    class _StubModel:
        def with_structured_output(self, schema):
            return _StubRunnable()

    result = asyncio.run(
        generate_json(
            model=_StubModel(), system="s", user="u", response_model=MovieInfo  # type: ignore[arg-type]
        )
    )
    assert result == {"name": "Inception", "year": 2010}


def test_failure_is_wrapped_in_llm_provider_error():
    class _BoomRunnable:
        async def ainvoke(self, messages):
            raise RuntimeError("boom")

    class _BoomModel:
        def with_structured_output(self, schema):
            return _BoomRunnable()

    with pytest.raises(LLMProviderError, match="boom") as excinfo:
        asyncio.run(
            generate_json(
                model=_BoomModel(), system="s", user="u", response_model=TitleOnly  # type: ignore[arg-type]
            )
        )
    assert isinstance(excinfo.value.__cause__, RuntimeError)


def test_openai_compatible_model_uses_json_mode_with_schema(monkeypatch):
    from langchain_openai import ChatOpenAI
    from pydantic import SecretStr

    captured: dict[str, Any] = {}

    class _StubRunnable:
        async def ainvoke(self, messages):
            captured["system_content"] = messages[0].content
            return MovieInfo(name="Inception", year=2010)

    def fake_with_structured_output(self, schema, **kwargs):
        captured["method"] = kwargs.get("method")
        return _StubRunnable()

    monkeypatch.setattr(
        ChatOpenAI, "with_structured_output", fake_with_structured_output
    )

    model = ChatOpenAI(model="x", api_key=SecretStr("dummy"))
    result = asyncio.run(
        generate_json(
            model=model,
            system="Be precise.",
            user="u",
            response_model=MovieInfo,
        )
    )

    assert result == {"name": "Inception", "year": 2010}
    assert captured["method"] == "json_mode"
    assert '"name"' in captured["system_content"]
    assert "JSON Schema" in captured["system_content"]


def test_non_openai_model_keeps_plain_system_prompt():
    class _StubRunnable:
        async def ainvoke(self, messages):
            assert messages[0].content == "s"
            assert "JSON Schema" not in messages[0].content
            return MovieInfo(name="Inception", year=2010)

    class _StubModel:
        def with_structured_output(self, schema):
            return _StubRunnable()

    result = asyncio.run(
        generate_json(
            model=_StubModel(), system="s", user="u", response_model=MovieInfo  # type: ignore[arg-type]
        )
    )
    assert result == {"name": "Inception", "year": 2010}
