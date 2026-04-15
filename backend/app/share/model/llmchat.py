import json
from typing import Literal

from pydantic import BaseModel, Field

MessageRole = Literal["system", "user", "assistant"]


class LLMChatMessage(BaseModel):
    role: MessageRole
    content: str


class LLMChat(BaseModel):
    messages: list[LLMChatMessage] = Field(default_factory=list)
    system: str

    def add_message(self, role: MessageRole, content: str) -> "LLMChat":
        self.messages.append(LLMChatMessage(role=role, content=content))
        return self

    def add_user(self, content: str) -> "LLMChat":
        return self.add_message("user", content)

    def add_assistant(self, content: str) -> "LLMChat":
        return self.add_message("assistant", content)

    def to_messages(self) -> list[dict[str, str]]:
        result = [{"role": "system", "content": self.system}]
        result.extend(
            {"role": message.role, "content": message.content}
            for message in self.messages
        )
        return result

def from_json(json_str: str) -> LLMChat:
    try:
        data = json.loads(json_str)
    except json.JSONDecodeError:
        raise ValueError("Invalid JSON")

    messages = [
        LLMChatMessage(
            role=msg.get("role", "user"),
            content=msg.get("content", ""),
        )
        for msg in data.get("messages", [])
        if isinstance(msg, dict)
    ]

    return LLMChat(
        system=data.get("system", ""),
        messages=messages,
    )

