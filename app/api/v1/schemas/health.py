from typing import Literal

from app.api.v1.schemas.base import APIModel


class ProviderHealth(APIModel):
    name: str
    healthy: bool
    base_url: str
    latency_ms: float | None = None
    detail: str | None = None


class HealthResponse(APIModel):
    status: Literal["ok", "degraded", "down"]
    active_provider: str | None
    model_loaded: bool
    primary: ProviderHealth
    fallback: ProviderHealth | None = None
