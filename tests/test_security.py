import pytest
from fastapi import HTTPException

from app.core.security import FixedWindowQuota, extract_api_key


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
