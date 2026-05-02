from fastapi import APIRouter, HTTPException, Response, status

from app.api.dependencies import AuthOnlySubjectDep, GatewayDep
from app.api.v1.schemas.health import HealthResponse
from app.core.exceptions import ProviderError

router = APIRouter(tags=["health"])


@router.get("/health", response_model=HealthResponse)
async def deep_health(gateway: GatewayDep, _subject: AuthOnlySubjectDep) -> dict:
    return await gateway.health()


@router.get("/models")
async def models(response: Response, gateway: GatewayDep, _subject: AuthOnlySubjectDep) -> dict:
    try:
        data, provider = await gateway.models()
        response.headers["X-LLM-Provider"] = provider
        return data
    except ProviderError as exc:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=str(exc)) from exc
