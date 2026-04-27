from typing import Any, Literal

from pydantic import Field, field_validator

from app.api.v1.schemas.base import APIModel


class ChatMessage(APIModel):
    role: Literal["system", "user", "assistant", "tool"]
    content: str | list[dict[str, Any]] | None = None
    name: str | None = None
    tool_call_id: str | None = None


class ChatCompletionRequest(APIModel):
    model: str | None = None
    messages: list[ChatMessage] = Field(min_length=1)
    temperature: float = Field(default=0.7, ge=0.0, le=2.0)
    top_p: float = Field(default=0.95, ge=0.0, le=1.0)
    max_tokens: int = Field(default=512, ge=1, le=4096)
    stream: bool = False

    # Common OpenAI-compatible optional knobs.
    frequency_penalty: float | None = Field(default=None, ge=-2.0, le=2.0)
    presence_penalty: float | None = Field(default=None, ge=-2.0, le=2.0)
    stop: str | list[str] | None = None

    @field_validator("messages")
    @classmethod
    def require_user_message(cls, messages: list[ChatMessage]) -> list[ChatMessage]:
        if not any(message.role == "user" for message in messages):
            raise ValueError("at least one user message is required")
        return messages

    def provider_payload(self, model: str) -> dict[str, Any]:
        payload = self.model_dump(exclude_none=True)
        payload["model"] = model
        return payload
