"""Custom exceptions for faceless YouTube automation."""

from __future__ import annotations


class YTFacelessError(Exception):
    """Base exception for all custom errors."""
    pass


class ConfigurationError(YTFacelessError):
    """Raised when configuration is invalid or missing."""
    pass


class APIError(YTFacelessError):
    """Base class for API-related errors."""
    
    def __init__(self, message: str, status_code: int | None = None, response_data: dict | None = None):
        super().__init__(message)
        self.status_code = status_code
        self.response_data = response_data


class N8NWebhookError(APIError):
    """Raised when n8n webhook fails."""
    pass


class FirecrawlError(APIError):
    """Raised when Firecrawl API fails."""
    pass


class BraveSearchError(APIError):
    """Raised when Brave Search API fails."""
    pass


class YouTubeAPIError(APIError):
    """Raised when YouTube Data API fails."""
    pass


class TTSError(YTFacelessError):
    """Raised when TTS generation fails."""
    pass


class VideoAssemblyError(YTFacelessError):
    """Raised when video assembly fails."""
    pass


class ContentValidationError(YTFacelessError):
    """Raised when content fails validation checks."""
    
    def __init__(self, message: str, validation_type: str, details: dict | None = None):
        super().__init__(message)
        self.validation_type = validation_type
        self.details = details or {}


class PolicyViolationError(ContentValidationError):
    """Raised when content violates YouTube policies."""
    pass


class CopyrightError(ContentValidationError):
    """Raised when content may have copyright issues."""
    pass


class ResearchError(YTFacelessError):
    """Raised when research/idea generation fails."""
    pass


class ScriptGenerationError(YTFacelessError):
    """Raised when script generation fails."""
    pass


class AssetCurationError(YTFacelessError):
    """Raised when asset curation/download fails."""
    pass


class AssetError(YTFacelessError):
    """Raised when asset operations fail."""
    pass


class TimelineError(YTFacelessError):
    """Raised when timeline operations fail."""
    pass


class ValidationError(YTFacelessError):
    """Raised when validation fails."""
    pass


class CacheError(YTFacelessError):
    """Raised when cache operations fail."""
    pass


class RateLimitError(APIError):
    """Raised when API rate limit is exceeded."""
    
    def __init__(self, message: str, retry_after: int | None = None):
        super().__init__(message)
        self.retry_after = retry_after


class RetryableError(YTFacelessError):
    """Base class for errors that should trigger a retry."""
    pass


class NonRetryableError(YTFacelessError):
    """Base class for errors that should not trigger a retry."""
    pass