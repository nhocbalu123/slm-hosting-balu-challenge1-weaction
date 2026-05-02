import pytest
from unittest.mock import AsyncMock

from app.core.config import Settings
from app.core.exceptions import ProviderRequestError, ProviderUnavailableError
from app.domains.vllm_service import LLMGateway


FAKE_RESPONSE = {
    "id": "chatcmpl-test",
    "object": "chat.completion",
    "choices": [{"index": 0, "message": {"role": "assistant", "content": "Hello!"}, "finish_reason": "stop"}],
}

PAYLOAD = {"model": "qwen", "messages": [{"role": "user", "content": "hi"}]}


@pytest.fixture()
def gateway() -> LLMGateway:
    settings = Settings(
        vllm_base_url="http://vllm:8000/v1",
        fallback_base_url="http://ollama:11434/v1",
        enable_fallback=True,
        api_keys="",
    )
    gw = LLMGateway(settings)
    gw.primary = AsyncMock()
    gw.primary.name = "vllm"
    gw.fallback = AsyncMock()
    gw.fallback.name = "ollama"
    return gw


async def test_gateway_uses_configured_provider_names() -> None:
    settings = Settings(
        primary_provider_name="ollama",
        fallback_provider_name="backup",
        enable_fallback=True,
        api_keys="",
    )
    gateway = LLMGateway(settings)

    assert gateway.primary.name == "ollama"
    assert gateway.fallback is not None
    assert gateway.fallback.name == "backup"
    await gateway.close()


async def test_primary_success(gateway: LLMGateway) -> None:
    gateway.primary.chat_completions.return_value = FAKE_RESPONSE

    result, provider = await gateway.chat_completions(PAYLOAD, request_id="r1", subject="s1")

    assert result == FAKE_RESPONSE
    assert provider == "vllm"
    gateway.fallback.chat_completions.assert_not_called()


async def test_primary_failure_triggers_fallback(gateway: LLMGateway) -> None:
    gateway.primary.chat_completions.side_effect = ProviderUnavailableError("vllm down")
    gateway.fallback.chat_completions.return_value = FAKE_RESPONSE

    result, provider = await gateway.chat_completions(PAYLOAD, request_id="r1", subject="s1")

    assert result == FAKE_RESPONSE
    assert provider == "ollama"


async def test_primary_request_error_does_not_trigger_fallback(gateway: LLMGateway) -> None:
    gateway.primary.chat_completions.side_effect = ProviderRequestError("bad request", provider_status_code=400)

    with pytest.raises(ProviderRequestError):
        await gateway.chat_completions(PAYLOAD, request_id="r1", subject="s1")

    gateway.fallback.chat_completions.assert_not_called()


async def test_both_providers_down(gateway: LLMGateway) -> None:
    gateway.primary.chat_completions.side_effect = ProviderUnavailableError("vllm down")
    gateway.fallback.chat_completions.side_effect = ProviderUnavailableError("ollama down")

    with pytest.raises(ProviderUnavailableError):
        await gateway.chat_completions(PAYLOAD, request_id="r1", subject="s1")
