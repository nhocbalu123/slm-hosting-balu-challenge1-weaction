import pytest
from fastapi import HTTPException
from starlette.requests import Request

from app.core.config import Settings
from app.core.security import FixedWindowQuota, api_key_matches, extract_api_key, require_api_key, subject_for_api_key


def test_extract_x_api_key() -> None:
    assert extract_api_key(None, "abc") == "abc"


def test_extract_bearer_token() -> None:
    assert extract_api_key("Bearer abc", None) == "abc"


def test_quota_blocks_after_limit() -> None:
    quota = FixedWindowQuota(requests_per_minute=1)
    quota.check("user")
    with pytest.raises(HTTPException) as exc:
        quota.check("user")
    assert exc.value.status_code == 429


def test_subject_for_api_key_is_stable_and_redacted() -> None:
    subject = subject_for_api_key("super-secret-key")

    assert subject == subject_for_api_key("super-secret-key")
    assert subject.startswith("api_key:")
    assert "super-secret-key" not in subject


def test_api_key_matches_uses_constant_time_compare(monkeypatch: pytest.MonkeyPatch) -> None:
    calls: list[tuple[str, str]] = []

    def fake_compare(left: str, right: str) -> bool:
        calls.append((left, right))
        return left == right

    monkeypatch.setattr("app.core.security.hmac.compare_digest", fake_compare)

    assert api_key_matches("super-secret-key", ["super-secret-key", "second-key"])
    assert calls == [("super-secret-key", "super-secret-key"), ("super-secret-key", "second-key")]


async def test_require_api_key_returns_redacted_subject() -> None:
    request = Request({"type": "http", "client": ("127.0.0.1", 12345), "headers": []})
    settings = Settings(api_keys="super-secret-key")
    quota = FixedWindowQuota(requests_per_minute=10)

    subject = await require_api_key(
        request=request,
        settings=settings,
        quota=quota,
        x_api_key="super-secret-key",
    )

    assert subject.startswith("api_key:")
    assert "super-secret-key" not in subject
    assert subject in quota._buckets
