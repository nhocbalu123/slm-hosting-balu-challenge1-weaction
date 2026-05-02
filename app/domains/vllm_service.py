import logging
import time
from typing import Any

from app.core.config import Settings
from app.core.exceptions import ProviderError
from app.services.openai_client import OpenAICompatibleClient

logger = logging.getLogger(__name__)


class LLMGateway:
    """Application layer for provider selection, timeout handling, and fallback."""

    def __init__(self, settings: Settings) -> None:
        self.settings = settings
        self.primary = OpenAICompatibleClient(
            name=settings.primary_provider_name,
            base_url=settings.vllm_base_url,
            api_key=settings.vllm_api_key,
            timeout_seconds=settings.primary_timeout_seconds,
            expected_model=settings.vllm_model,
        )
        self.fallback = (
            OpenAICompatibleClient(
                name=settings.fallback_provider_name,
                base_url=settings.fallback_base_url,
                api_key=settings.fallback_api_key,
                timeout_seconds=settings.fallback_timeout_seconds,
                expected_model=settings.fallback_model,
            )
            if settings.enable_fallback
            else None
        )

    async def close(self) -> None:
        await self.primary.close()
        if self.fallback:
            await self.fallback.close()

    async def chat_completions(self, payload: dict[str, Any], request_id: str, subject: str) -> tuple[dict[str, Any], str]:
        """Send to vLLM first, then optional Ollama fallback.

        Returns: `(provider_response, provider_name)`.
        """
        start = time.perf_counter()
        primary_payload = {**payload, "model": self.settings.vllm_model}
        try:
            result = await self.primary.chat_completions(primary_payload)
            latency_ms = round((time.perf_counter() - start) * 1000, 2)
            logger.info(
                "chat completion succeeded",
                extra={
                    "request_id": request_id,
                    "subject": subject,
                    "provider": self.primary.name,
                    "latency_ms": latency_ms,
                },
            )
            return result, self.primary.name
        except ProviderError as primary_error:
            logger.warning(
                "primary provider failed",
                extra={
                    "request_id": request_id,
                    "subject": subject,
                    "provider": self.primary.name,
                    "error": str(primary_error),
                },
            )
            if not self.fallback:
                raise

        fallback = self.fallback
        fallback_start = time.perf_counter()
        fallback_payload = {**payload, "model": self.settings.fallback_model}
        try:
            result = await fallback.chat_completions(fallback_payload)
            latency_ms = round((time.perf_counter() - fallback_start) * 1000, 2)
            logger.info(
                "chat completion succeeded via fallback",
                extra={
                    "request_id": request_id,
                    "subject": subject,
                    "provider": fallback.name,
                    "latency_ms": latency_ms,
                },
            )
            return result, fallback.name
        except ProviderError:
            logger.exception(
                "fallback provider failed",
                extra={
                    "request_id": request_id,
                    "subject": subject,
                    "provider": fallback.name,
                },
            )
            raise

    async def models(self) -> tuple[dict[str, Any], str]:
        primary_health = await self.primary.health()
        if primary_health["healthy"]:
            return await self.primary.models(), self.primary.name
        if self.fallback:
            fallback_health = await self.fallback.health()
            if fallback_health["healthy"]:
                return await self.fallback.models(), self.fallback.name
        raise ProviderError("no healthy provider available")

    async def health(self) -> dict[str, Any]:
        primary = await self.primary.health()
        fallback_provider = self.fallback
        fallback = await fallback_provider.health() if fallback_provider else None

        if primary["healthy"]:
            status = "ok"
            active_provider = self.primary.name
            model_loaded = True
        elif fallback and fallback["healthy"]:
            assert fallback_provider is not None
            status = "degraded"
            active_provider = fallback_provider.name
            model_loaded = True
        else:
            status = "down"
            active_provider = None
            model_loaded = False

        return {
            "status": status,
            "active_provider": active_provider,
            "model_loaded": model_loaded,
            "primary": primary,
            "fallback": fallback,
        }
