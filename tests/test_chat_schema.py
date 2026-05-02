import pytest
from pydantic import ValidationError

from app.api.v1.schemas.chat import ChatCompletionRequest


def test_empty_messages_rejected() -> None:
    with pytest.raises(ValidationError):
        ChatCompletionRequest(messages=[])


def test_no_user_message_rejected() -> None:
    with pytest.raises(ValidationError):
        ChatCompletionRequest(messages=[{"role": "system", "content": "Be helpful."}])


@pytest.mark.parametrize("content", [None, "", "   ", []])
def test_empty_user_content_rejected(content: object) -> None:
    with pytest.raises(ValidationError):
        ChatCompletionRequest(messages=[{"role": "user", "content": content}])


def test_temperature_out_of_range() -> None:
    with pytest.raises(ValidationError):
        ChatCompletionRequest(
            messages=[{"role": "user", "content": "hi"}],
            temperature=3.0,
        )
