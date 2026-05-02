from typing import Annotated

from fastapi import Depends, Header, Request

from app.core.config import Settings, get_settings
from app.core.security import FixedWindowQuota, authenticate_api_key, require_api_key
from app.domains.vllm_service import LLMGateway


def get_quota(request: Request) -> FixedWindowQuota:
    return request.app.state.quota


def get_llm_gateway(request: Request) -> LLMGateway:
    return request.app.state.llm_gateway


SettingsDep = Annotated[Settings, Depends(get_settings)]
QuotaDep = Annotated[FixedWindowQuota, Depends(get_quota)]
GatewayDep = Annotated[LLMGateway, Depends(get_llm_gateway)]


async def authenticated_subject(
    request: Request,
    settings: SettingsDep,
    quota: QuotaDep,
    authorization: str | None = Header(default=None),
    x_api_key: str | None = Header(default=None, alias="X-API-Key"),
) -> str:
    return await require_api_key(
        request=request,
        settings=settings,
        quota=quota,
        authorization=authorization,
        x_api_key=x_api_key,
    )


async def auth_only_subject(
    request: Request,
    settings: SettingsDep,
    authorization: str | None = Header(default=None),
    x_api_key: str | None = Header(default=None, alias="X-API-Key"),
) -> str:
    return await authenticate_api_key(
        request=request,
        settings=settings,
        authorization=authorization,
        x_api_key=x_api_key,
    )


AuthSubjectDep = Annotated[str, Depends(authenticated_subject)]
AuthOnlySubjectDep = Annotated[str, Depends(auth_only_subject)]
