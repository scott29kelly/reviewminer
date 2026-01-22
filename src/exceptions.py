"""Custom exceptions for Review Miner."""


class ReviewMinerError(Exception):
    """Base exception for Review Miner.
    
    All custom exceptions in this application inherit from this class,
    making it easy to catch any Review Miner-specific error.
    """
    pass


class ConfigError(ReviewMinerError):
    """Configuration loading or validation error.
    
    Raised when:
    - config.yaml is malformed or missing required fields
    - Environment variables are missing or invalid
    - API keys are not configured
    """
    pass


class ScraperError(ReviewMinerError):
    """Base exception for scraper-related errors.
    
    Raised when a scraper encounters an error that prevents
    it from completing its task.
    """
    pass


class RateLimitError(ScraperError):
    """Rate limiting detected by target website.
    
    Raised when:
    - HTTP 429 response received
    - CAPTCHA or bot detection triggered
    - Too many requests in a short time period
    """
    
    def __init__(self, message: str = "Rate limit exceeded", retry_after: int | None = None):
        super().__init__(message)
        self.retry_after = retry_after


class ScraperTimeoutError(ScraperError):
    """Scraper request timed out.
    
    Raised when a page load or request exceeds the configured timeout.
    """
    pass


class ScraperParseError(ScraperError):
    """Failed to parse scraped content.
    
    Raised when:
    - Expected HTML elements are not found
    - Page structure has changed
    - Content is malformed
    """
    pass


class AnalyzerError(ReviewMinerError):
    """Claude API or analysis error.
    
    Raised when:
    - API call fails
    - Response parsing fails
    - Invalid response format
    """
    pass


class AnalyzerAPIError(AnalyzerError):
    """Claude API communication error.
    
    Raised when the API call itself fails (network, auth, rate limit).
    """
    pass


class AnalyzerParseError(AnalyzerError):
    """Failed to parse Claude's response.
    
    Raised when the response JSON is malformed or missing expected fields.
    """
    pass


class DatabaseError(ReviewMinerError):
    """Database operation error.
    
    Raised when:
    - Database connection fails
    - Query execution fails
    - Schema is corrupted
    """
    pass


class ExportError(ReviewMinerError):
    """Export operation error.
    
    Raised when:
    - Cannot write to output file
    - Export format is invalid
    - Data serialization fails
    """
    pass
