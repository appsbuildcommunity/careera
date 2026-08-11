import json

import pytest
from langchain_core.messages import HumanMessage, SystemMessage
from langchain_core.runnables import Runnable

from app.share.service.llm.exceptions import LLMProviderError
from app.share.service.llm.mock import MockChatModel

PROMPT_PAYLOADS = {
    "career analysis": ["profile_insight", "recommendations"],
    "career path": ["title", "nodes", "missing_skills"],
    "learning template": ["title", "content"],
    "project template": ["title", "tasks"],
    "interview template": ["title", "questions"],
}


@pytest.fixture
def model():
    return MockChatModel()


def test_llm_type_is_mock(model):
    assert model._llm_type == "mock"


def test_with_structured_output_returns_runnable(model):
    assert isinstance(model.with_structured_output({"type": "object"}), Runnable)


def test_structured_output_returns_canned_dict(model):
    runnable = model.with_structured_output({"type": "object"})
    result = runnable.invoke(
        [SystemMessage(content="sys"), HumanMessage(content="career analysis")]
    )
    assert isinstance(result, dict)
    assert "profile_insight" in result


@pytest.mark.parametrize(("prompt", "expected_keys"), list(PROMPT_PAYLOADS.items()))
def test_canned_payloads_for_each_prompt_type(model, prompt, expected_keys):
    runnable = model.with_structured_output({"type": "object"})
    result = runnable.invoke([HumanMessage(content=prompt)])
    assert isinstance(result, dict)
    for key in expected_keys:
        assert key in result


def test_unknown_prompt_raises(model):
    runnable = model.with_structured_output({"type": "object"})
    with pytest.raises(LLMProviderError, match="does not recognize"):
        runnable.invoke([HumanMessage(content="something else entirely")])


def test_plain_invoke_returns_canned_json(model):
    message = model.invoke([HumanMessage(content="career analysis")])
    payload = json.loads(message.content)
    assert "profile_insight" in payload
