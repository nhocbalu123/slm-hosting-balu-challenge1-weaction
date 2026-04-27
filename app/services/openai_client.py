import time
from typing import Any

import httpx

from app.core.exceptions import ProviderTimeoutError, ProviderUnavailableError


class OpenAICompatibleClient:
    """Async client for OpenAI-compatible model servers such as vLLM and Ollama."""

    def __init__(self, name: str, base_url: str, api_key: str, timeout_seconds: float) -> None:
        self.name = name
        self.base_url = base_url.rstrip("/")
        self.api_key = api_key
        self.timeout_seconds = timeout_seconds
        self._client = httpx.AsyncClient(
            base_url=self.base_url,
            timeout=httpx.Timeout(timeout_seconds),
            headers={"Authorization": f"Bearer {api_key}"},
        )

    async def close(self) -> None:
        await self._client.aclose()

    async def chat_completions(self, payload: dict[str, Any]) -> dict[str, Any]:
        try:
            response = await self._client.post("/chat/completions", json=payload)
        except httpx.TimeoutException as exc:
            raise ProviderTimeoutError(f"{self.name} timed out after {self.timeout_seconds}s") from exc
        except httpx.HTTPError as exc:
            raise ProviderUnavailableError(f"{self.name} connection error: {exc}") from exc

        if response.status_code >= 500:
            raise ProviderUnavailableError(f"{self.name} server error: {response.status_code} {response.text[:300]}")
        if response.status_code >= 400:
            raise ProviderUnavailableError(f"{self.name} rejected request: {response.status_code} {response.text[:300]}")
        return response.json()

    async def models(self) -> dict[str, Any]:
        try:
            response = await self._client.get("/models")
            response.raise_for_status()
            return response.json()
        except httpx.TimeoutException as exc:
            raise ProviderTimeoutError(f"{self.name} /models timed out") from exc
        except httpx.HTTPError as exc:
            raise ProviderUnavailableError(f"{self.name} /models error: {exc}") from exc

    async def health(self) -> dict[str, Any]:
        start = time.perf_counter()
        try:
            models = await self.models()
            latency_ms = round((time.perf_counter() - start) * 1000, 2)
            count = len(models.get("data", [])) if isinstance(models, dict) else None
            return {
                "name": self.name,
                "healthy": True,
                "base_url": self.base_url,
                "latency_ms": latency_ms,
                "detail": f"models endpoint ok; model_count={count}",
            }
        except Exception as exc:  # noqa: BLE001 - health should always return a status payload
            latency_ms = round((time.perf_counter() - start) * 1000, 2)
            return {
                "name": self.name,
                "healthy": False,
                "base_url": self.base_url,
                "latency_ms": latency_ms,
                "detail": str(exc),
            }
