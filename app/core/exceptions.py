class ProviderError(RuntimeError):
    """Base error for provider calls."""


class ProviderTimeoutError(ProviderError):
    """Raised when a provider does not respond before timeout."""


class ProviderRequestError(ProviderError):
    """Raised when the provider rejects an otherwise reachable request."""

    def __init__(self, message: str, provider_status_code: int) -> None:
        super().__init__(message)
        self.provider_status_code = provider_status_code


class ProviderUnavailableError(ProviderError):
    """Raised when a provider returns an unhealthy response or cannot be reached."""
