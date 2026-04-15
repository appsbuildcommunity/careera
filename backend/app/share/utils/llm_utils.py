import os
from typing import cast
from openai.types.chat import ChatCompletionMessageParam

from dotenv import load_dotenv
from openai import AsyncOpenAI
from app.share.model.llmchat import LLMChat

load_dotenv()


async def call_llm(chat: LLMChat) -> str:
    if not chat.messages and not chat.system:
        raise ValueError("chat cannot be empty")

    api_key = os.getenv("OLLAMA_API_KEY")
    if not api_key:
        raise ValueError("OLLAMA_API_KEY is required")

    base_url = os.getenv("OLLAMA_OPENAI_BASE_URL", "http://localhost:11434/v1/")
    model = os.getenv("OLLAMA_MODEL", "kimi-k2.5:cloud")

    client = AsyncOpenAI(api_key=api_key, base_url=base_url)

    conversations = chat.to_messages()

    response = await client.chat.completions.create(
        model=model,
        messages=cast(list[ChatCompletionMessageParam], conversations),
    )

    if not response.choices:
        return ""

    content = response.choices[0].message.content
    return content.strip() if content else ""

