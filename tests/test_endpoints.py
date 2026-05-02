from unittest.mock import AsyncMock

import pytest
from fastapi.testclient import TestClient

from app.api.dependencies import authenticated_subject, get_llm_gateway, get_quota
from app.core.config import Settings, get_settings
from app.core.exceptions import ProviderRequestError, ProviderUnavailableError
from app.core.security import FixedWindowQuota
from app.main import app


FAKE_RESPONSE = {
    "id": "chatcmpl-test",
    "object": "chat.completion",
    "choices": [{"index": 0, "message": {"role": "assistant", "content": "Hello!"}, "finish_reason": "stop"}],
}

VALID_PAYLOAD = {"messages": [{"role": "user", "content": "hi"}]}
HEALTH_RESPONSE = {
    "status": "ok",
    "active_provider": "vllm",
    "model_loaded": True,
    "primary": {
        "name": "vllm",
        "healthy": True,
        "base_url": "http://vllm:8000/v1",
        "latency_ms": 1.0,
        "detail": "models ok; count=1",
    },
    "fallback": None,
}


@pytest.fixture()
def mock_gateway() -> AsyncMock:
    return AsyncMock()


@pytest.fixture()
def client(mock_gateway: AsyncMock) -> TestClient:
    app.dependency_overrides[get_llm_gateway] = lambda: mock_gateway
    app.dependency_overrides[get_quota] = lambda: FixedWindowQuota(requests_per_minute=1000)
    app.dependency_overrides[authenticated_subject] = lambda: "test-subject"
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()


def test_stream_rejected(client: TestClient, mock_gateway: AsyncMock) -> None:
    resp = client.post("/v1/chat/completions", json={**VALID_PAYLOAD, "stream": True})
    assert resp.status_code == 400
    mock_gateway.chat_completions.assert_not_called()


def test_chat_returns_provider_header(client: TestClient, mock_gateway: AsyncMock) -> None:
    mock_gateway.chat_completions.return_value = (FAKE_RESPONSE, "vllm")

    resp = client.post("/v1/chat/completions", json=VALID_PAYLOAD)

    assert resp.status_code == 200
    assert resp.headers["x-llm-provider"] == "vllm"
    assert resp.json()["choices"][0]["message"]["content"] == "Hello!"


def test_both_down_returns_503(client: TestClient, mock_gateway: AsyncMock) -> None:
    mock_gateway.chat_completions.side_effect = ProviderUnavailableError("all providers down")

    resp = client.post("/v1/chat/completions", json=VALID_PAYLOAD)

    assert resp.status_code == 503


def test_provider_request_error_returns_400(client: TestClient, mock_gateway: AsyncMock) -> None:
    mock_gateway.chat_completions.side_effect = ProviderRequestError("context length exceeded", provider_status_code=400)

    resp = client.post("/v1/chat/completions", json=VALID_PAYLOAD)

    assert resp.status_code == 400
    assert "rejected request" in resp.json()["detail"]


def test_deep_health_does_not_consume_chat_quota(mock_gateway: AsyncMock) -> None:
    quota = FixedWindowQuota(requests_per_minute=1)
    mock_gateway.health.return_value = HEALTH_RESPONSE
    app.dependency_overrides[get_llm_gateway] = lambda: mock_gateway
    app.dependency_overrides[get_quota] = lambda: quota
    app.dependency_overrides[get_settings] = lambda: Settings(api_keys="test-key")

    with TestClient(app) as c:
        first = c.get("/v1/health", headers={"X-API-Key": "test-key"})
        second = c.get("/v1/health", headers={"X-API-Key": "test-key"})

    app.dependency_overrides.clear()

    assert first.status_code == 200
    assert second.status_code == 200
    assert quota._buckets == {}
