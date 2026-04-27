class ProviderError(RuntimeError):
    """Base error for provider calls."""


class ProviderTimeoutError(ProviderError):
    """Raised when a provider does not respond before timeout."""


class ProviderUnavailableError(ProviderError):
    """Raised when a provider returns an unhealthy response or cannot be reached."""
