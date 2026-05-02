import httpx
import pytest

from app.core.exceptions import ProviderRequestError, ProviderTimeoutError, ProviderUnavailableError
from app.services.openai_client import OpenAICompatibleClient


def make_client(handler: httpx.MockTransport) -> OpenAICompatibleClient:
    return OpenAICompatibleClient(
        name="test-provider",
        base_url="http://provider.test/v1",
        api_key="test-key",
        timeout_seconds=1,
        expected_model="expected-model",
        transport=handler,
    )


@pytest.mark.parametrize("status_code", [400, 422])
async def test_chat_4xx_raises_request_error(status_code: int) -> None:
    transport = httpx.MockTransport(lambda request: httpx.Response(status_code, text="bad request"))
    client = make_client(transport)

    with pytest.raises(ProviderRequestError) as exc:
        await client.chat_completions({"messages": [{"role": "user", "content": "hi"}]})

    assert exc.value.provider_status_code == status_code
    await client.close()


async def test_chat_5xx_raises_unavailable_error() -> None:
    transport = httpx.MockTransport(lambda request: httpx.Response(503, text="down"))
    client = make_client(transport)

    with pytest.raises(ProviderUnavailableError):
        await client.chat_completions({"messages": [{"role": "user", "content": "hi"}]})

    await client.close()


async def test_chat_timeout_raises_timeout_error() -> None:
    def raise_timeout(request: httpx.Request) -> httpx.Response:
        raise httpx.ReadTimeout("timed out", request=request)

    client = make_client(httpx.MockTransport(raise_timeout))

    with pytest.raises(ProviderTimeoutError):
        await client.chat_completions({"messages": [{"role": "user", "content": "hi"}]})

    await client.close()


async def test_chat_connection_error_raises_unavailable_error() -> None:
    def raise_connection_error(request: httpx.Request) -> httpx.Response:
        raise httpx.ConnectError("connection refused", request=request)

    client = make_client(httpx.MockTransport(raise_connection_error))

    with pytest.raises(ProviderUnavailableError):
        await client.chat_completions({"messages": [{"role": "user", "content": "hi"}]})

    await client.close()


async def test_chat_non_json_success_raises_unavailable_error() -> None:
    transport = httpx.MockTransport(lambda request: httpx.Response(200, text="not json"))
    client = make_client(transport)

    with pytest.raises(ProviderUnavailableError):
        await client.chat_completions({"messages": [{"role": "user", "content": "hi"}]})

    await client.close()


async def test_models_failure_raises_unavailable_error() -> None:
    transport = httpx.MockTransport(lambda request: httpx.Response(503, text="down"))
    client = make_client(transport)

    with pytest.raises(ProviderUnavailableError):
        await client.models()

    await client.close()


async def test_health_reports_model_mismatch() -> None:
    transport = httpx.MockTransport(
        lambda request: httpx.Response(200, json={"data": [{"id": "other-model"}]})
    )
    client = make_client(transport)

    health = await client.health()

    assert health["healthy"] is False
    assert health["detail"] == "configured model 'expected-model' not found in provider (available: ['other-model'])"
    await client.close()
