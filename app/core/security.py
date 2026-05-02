import hashlib
import hmac
import time
from dataclasses import dataclass, field

from fastapi import HTTPException, Request, status

from app.core.config import Settings


@dataclass
class FixedWindowQuota:
    """Simple in-memory quota for portfolio/demo use.

    This is intentionally minimal. Replace with Redis or a gateway quota in real production.
    """

    requests_per_minute: int
    _buckets: dict[str, tuple[int, float]] = field(default_factory=dict)

    def check(self, subject: str) -> None:
        now = time.time()
        count, reset_at = self._buckets.get(subject, (0, now + 60))
        if now >= reset_at:
            count = 0
            reset_at = now + 60
        if count >= self.requests_per_minute:
            seconds = max(1, int(reset_at - now))
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail=f"quota exceeded; retry in {seconds}s",
                headers={"Retry-After": str(seconds)},
            )
        self._buckets[subject] = (count + 1, reset_at)


def extract_api_key(authorization: str | None, x_api_key: str | None) -> str | None:
    if x_api_key:
        return x_api_key.strip()
    if authorization and authorization.lower().startswith("bearer "):
        return authorization.split(" ", 1)[1].strip()
    return None


def subject_for_api_key(api_key: str) -> str:
    digest = hashlib.sha256(api_key.encode("utf-8")).hexdigest()[:12]
    return f"api_key:{digest}"


def api_key_matches(provided_key: str, allowed_keys: list[str]) -> bool:
    matched = False
    for allowed_key in allowed_keys:
        matched |= hmac.compare_digest(provided_key, allowed_key)
    return matched


async def require_api_key(
    request: Request,
    settings: Settings,
    quota: FixedWindowQuota,
    authorization: str | None = None,
    x_api_key: str | None = None,
) -> str:
    key = extract_api_key(authorization, x_api_key)
    if settings.api_keys:
        if key is None or not api_key_matches(key, settings.api_keys):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="missing or invalid API key",
            )
        subject = subject_for_api_key(key)
    else:
        subject = request.client.host if request.client else "anonymous"
    quota.check(subject)
    return subject
