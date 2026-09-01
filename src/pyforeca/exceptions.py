class ForecaError(Exception):
    """Base exception for pyforeca."""


class ForecaConnectionError(ForecaError):
    """Could not reach the Foreca API."""


class ForecaAuthError(ForecaError):
    """API key was rejected."""


class ForecaRateLimitError(ForecaError):
    """Request or daily rate limit exceeded."""
