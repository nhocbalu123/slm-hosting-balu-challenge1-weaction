from app.core.config import Settings


def test_api_keys_split_from_comma_string() -> None:
    settings = Settings(api_keys="a,b, c")
    assert settings.api_keys == ["a", "b", "c"]


def test_base_urls_strip_trailing_slash() -> None:
    settings = Settings(vllm_base_url="http://example.com/v1/", fallback_base_url="http://fallback/v1/")
    assert settings.vllm_base_url == "http://example.com/v1"
    assert settings.fallback_base_url == "http://fallback/v1"


def test_provider_names_are_configurable() -> None:
    settings = Settings(primary_provider_name="ollama", fallback_provider_name="backup")

    assert settings.primary_provider_name == "ollama"
    assert settings.fallback_provider_name == "backup"
