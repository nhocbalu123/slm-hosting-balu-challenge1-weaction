from fastapi import APIRouter, HTTPException, Request, Response, status

from app.api.dependencies import AuthSubjectDep, GatewayDep
from app.api.v1.schemas.chat import ChatCompletionRequest
from app.core.exceptions import ProviderError

router = APIRouter(tags=["chat"])


@router.post("/chat/completions")
async def chat_completions(
    payload: ChatCompletionRequest,
    request: Request,
    response: Response,
    gateway: GatewayDep,
    subject: AuthSubjectDep,
) -> dict:
    if payload.stream:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="stream=true is not supported by this wrapper yet; use non-streaming requests for the challenge demo",
        )

    request_id = getattr(request.state, "request_id", "unknown")
    provider_payload = payload.provider_payload(model=payload.model or "default")
    try:
        data, provider = await gateway.chat_completions(provider_payload, request_id=request_id, subject=subject)
        response.headers["X-LLM-Provider"] = provider
        response.headers["X-Request-ID"] = request_id
        return data
    except ProviderError as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"no model provider available: {exc}",
        ) from exc
