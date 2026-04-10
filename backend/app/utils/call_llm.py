import os
from typing import Any, cast
from openai.types.chat import ChatCompletionMessageParam

from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()


async def call_llm(conversations: list[dict[str, Any]]) -> str:
    """Send chat messages to an llm."""
    if not conversations:
        raise ValueError("conversations cannot be empty")

    api_key = os.getenv("OLLAMA_API_KEY")
    if not api_key:
        raise ValueError("OLLAMA_API_KEY is required")

    base_url = os.getenv("OLLAMA_OPENAI_BASE_URL", "http://localhost:11434/v1/")
    model = os.getenv("OLLAMA_MODEL", "kimi-k2.5:cloud")

    client = OpenAI(api_key=api_key, base_url=base_url)

    response = client.chat.completions.create(
        model=model,
        messages=cast(list[ChatCompletionMessageParam], conversations),
    )

    content = response.choices[0].message.content
    if not content:
        return ""
    return content.strip()
