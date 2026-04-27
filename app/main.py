from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.api.v1.router import api_router
from app.core.config import get_settings
from app.core.logging import RequestLogMiddleware, configure_logging
from app.core.security import FixedWindowQuota
from app.domains.vllm_service import LLMGateway


@asynccontextmanager
async def lifespan(app: FastAPI):
    settings = get_settings()
    configure_logging(settings)
    app.state.llm_gateway = LLMGateway(settings)
    app.state.quota = FixedWindowQuota(settings.requests_per_minute)
    yield
    await app.state.llm_gateway.close()


settings = get_settings()
app = FastAPI(
    title=settings.app_name,
    version="0.1.0",
    description="FastAPI wrapper for a self-hosted Qwen SLM behind vLLM/Ollama.",
    lifespan=lifespan,
)
app.add_middleware(RequestLogMiddleware)
app.include_router(api_router)


@app.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok", "service": settings.app_name}
