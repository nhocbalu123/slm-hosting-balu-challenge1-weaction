from unittest.mock import AsyncMock

import pytest
from fastapi.testclient import TestClient

from app.api.dependencies import authenticated_subject, get_llm_gateway, get_quota
from app.core.exceptions import ProviderUnavailableError
from app.core.security import FixedWindowQuota
from app.main import app


FAKE_RESPONSE = {
    "id": "chatcmpl-test",
    "object": "chat.completion",
    "choices": [{"index": 0, "message": {"role": "assistant", "content": "Hello!"}, "finish_reason": "stop"}],
}

VALID_PAYLOAD = {"messages": [{"role": "user", "content": "hi"}]}


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
