import time
from typing import Any

import httpx

from app.core.exceptions import ProviderRequestError, ProviderTimeoutError, ProviderUnavailableError


class OpenAICompatibleClient:
    """Async client for OpenAI-compatible model servers such as vLLM and Ollama."""

    def __init__(
        self,
        name: str,
        base_url: str,
        api_key: str,
        timeout_seconds: float,
        expected_model: str | None = None,
        transport: httpx.AsyncBaseTransport | None = None,
    ) -> None:
        self.name = name
        self.base_url = base_url.rstrip("/")
        self.api_key = api_key
        self.timeout_seconds = timeout_seconds
        self.expected_model = expected_model
        self._client = httpx.AsyncClient(
            base_url=self.base_url,
            timeout=httpx.Timeout(timeout_seconds),
            headers={"Authorization": f"Bearer {api_key}"},
            transport=transport,
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
            raise ProviderRequestError(
                f"{self.name} rejected request: {response.status_code} {response.text[:300]}",
                provider_status_code=response.status_code,
            )
        try:
            return response.json()
        except ValueError as exc:
            raise ProviderUnavailableError(
                f"{self.name} returned non-JSON response (status {response.status_code})"
            ) from exc

    async def models(self) -> dict[str, Any]:
        try:
            response = await self._client.get("/models")
            response.raise_for_status()
            try:
                return response.json()
            except ValueError as exc:
                raise ProviderUnavailableError(
                    f"{self.name} /models returned non-JSON response"
                ) from exc
        except httpx.TimeoutException as exc:
            raise ProviderTimeoutError(f"{self.name} /models timed out") from exc
        except httpx.HTTPError as exc:
            raise ProviderUnavailableError(f"{self.name} /models error: {exc}") from exc

    async def health(self) -> dict[str, Any]:
        start = time.perf_counter()
        try:
            models = await self.models()
            latency_ms = round((time.perf_counter() - start) * 1000, 2)
            model_ids = [m.get("id") for m in models.get("data", [])] if isinstance(models, dict) else []
            model_ok = self.expected_model is None or self.expected_model in model_ids
            detail = (
                f"models ok; count={len(model_ids)}"
                if model_ok
                else f"configured model '{self.expected_model}' not found in provider (available: {model_ids})"
            )
            return {
                "name": self.name,
                "healthy": model_ok,
                "base_url": self.base_url,
                "latency_ms": latency_ms,
                "detail": detail,
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
