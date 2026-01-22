"""Claude API integration for pain point extraction."""

import json
import logging
import re
from dataclasses import dataclass, field
from typing import List, Optional

import anthropic
from tenacity import (
    retry,
    retry_if_exception_type,
    stop_after_attempt,
    wait_exponential,
    before_sleep_log,
)

from src.exceptions import AnalyzerAPIError, AnalyzerError, AnalyzerParseError
from src.logging_config import get_logger
from src.models import ExtractedPainPoint, Review
from src.prompts import PAIN_POINT_EXTRACTOR


logger = get_logger(__name__)


@dataclass
class AnalysisResult:
    """Result of batch analysis with failure tracking."""
    
    pain_points: List[ExtractedPainPoint] = field(default_factory=list)
    successful_batches: int = 0
    failed_batches: int = 0
    total_reviews_processed: int = 0
    errors: List[str] = field(default_factory=list)
    
    @property
    def has_failures(self) -> bool:
        """Check if any batches failed."""
        return self.failed_batches > 0
    
    @property
    def success_rate(self) -> float:
        """Calculate success rate as percentage."""
        total = self.successful_batches + self.failed_batches
        if total == 0:
            return 0.0
        return (self.successful_batches / total) * 100


class PainPointAnalyzer:
    """Analyzes reviews using Claude API to extract pain points."""
    
    # Retryable exceptions from the Anthropic SDK
    RETRYABLE_EXCEPTIONS = (
        anthropic.APIConnectionError,
        anthropic.RateLimitError,
        anthropic.InternalServerError,
    )
    
    def __init__(
        self,
        api_key: str,
        model: str = "claude-sonnet-4-5-20250929",
        max_retries: int = 3,
    ):
        if not api_key:
            raise ValueError("Anthropic API key is required")
        self.client = anthropic.Anthropic(api_key=api_key)
        self.model = model
        self.max_retries = max_retries
        logger.debug("Initialized PainPointAnalyzer with model=%s", model)
    
    def analyze_batch_sync(
        self,
        reviews: List[Review],
        batch_size: int = 20,
    ) -> List[ExtractedPainPoint]:
        """
        Analyze reviews in batches synchronously.
        Returns extracted pain points.
        
        Args:
            reviews: List of reviews to analyze
            batch_size: Number of reviews per API call
        
        Returns:
            List of extracted pain points
        
        Raises:
            AnalyzerError: If analysis fails completely
        """
        result = self.analyze_with_result(reviews, batch_size)
        return result.pain_points
    
    def analyze_with_result(
        self,
        reviews: List[Review],
        batch_size: int = 20,
        fail_fast: bool = False,
    ) -> AnalysisResult:
        """
        Analyze reviews with graceful degradation and detailed result tracking.
        
        Continues processing even if some batches fail, collecting partial results.
        
        Args:
            reviews: List of reviews to analyze
            batch_size: Number of reviews per API call
            fail_fast: If True, stop on first failure
        
        Returns:
            AnalysisResult with pain points and failure tracking
        """
        result = AnalysisResult()
        
        if not reviews:
            logger.info("No reviews to analyze")
            return result
        
        total_batches = (len(reviews) + batch_size - 1) // batch_size
        logger.info("Starting analysis of %d reviews in %d batches", len(reviews), total_batches)
        
        for i in range(0, len(reviews), batch_size):
            batch = reviews[i:i + batch_size]
            batch_num = i // batch_size + 1
            
            logger.debug("Processing batch %d/%d with %d reviews", batch_num, total_batches, len(batch))
            
            try:
                pain_points = self._process_single_batch(batch)
                result.pain_points.extend(pain_points)
                result.successful_batches += 1
                result.total_reviews_processed += len(batch)
                logger.debug("Batch %d extracted %d pain points", batch_num, len(pain_points))
                
            except (AnalyzerError, anthropic.APIError) as e:
                error_msg = f"Batch {batch_num} failed: {e}"
                logger.warning(error_msg)
                result.failed_batches += 1
                result.errors.append(error_msg)
                
                if fail_fast:
                    logger.error("Fail fast enabled, stopping analysis")
                    break
                
                # Continue to next batch
                continue
        
        # Log summary
        if result.has_failures:
            logger.warning(
                "Analysis completed with failures: %d/%d batches succeeded (%.1f%% success rate)",
                result.successful_batches,
                result.successful_batches + result.failed_batches,
                result.success_rate,
            )
        else:
            logger.info(
                "Analysis completed successfully: %d pain points from %d reviews",
                len(result.pain_points),
                result.total_reviews_processed,
            )
        
        return result
    
    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=30),
        retry=retry_if_exception_type((
            anthropic.APIConnectionError,
            anthropic.RateLimitError,
            anthropic.InternalServerError,
        )),
        before_sleep=before_sleep_log(logger, logging.WARNING),
        reraise=True,
    )
    def _process_single_batch(self, batch: List[Review]) -> List[ExtractedPainPoint]:
        """
        Process a single batch of reviews with retry logic.
        
        Args:
            batch: List of reviews to process
        
        Returns:
            List of extracted pain points
        
        Raises:
            AnalyzerAPIError: If API call fails
            AnalyzerParseError: If response parsing fails
        """
        batch_text = self._format_reviews(batch)
        
        try:
            response = self.client.messages.create(
                model=self.model,
                max_tokens=4096,
                system=PAIN_POINT_EXTRACTOR,
                messages=[{
                    "role": "user",
                    "content": f"Analyze these reviews and extract pain points:\n\n{batch_text}"
                }]
            )
        except anthropic.APIError as e:
            logger.error("Claude API error: %s", e)
            raise AnalyzerAPIError(f"API call failed: {e}") from e
        
        response_text = response.content[0].text
        logger.debug("Received response with %d characters", len(response_text))
        
        try:
            pain_points = self._parse_response(response_text)
        except Exception as e:
            logger.error("Failed to parse response: %s", e)
            raise AnalyzerParseError(f"Failed to parse response: {e}") from e
        
        return pain_points
    
    async def analyze_batch(
        self,
        reviews: List[Review],
        batch_size: int = 20,
    ) -> List[ExtractedPainPoint]:
        """
        Analyze reviews in batches asynchronously.
        Returns extracted pain points.
        """
        # For now, use sync version
        # Can be updated to use async client if needed
        return self.analyze_batch_sync(reviews, batch_size)
    
    def _format_reviews(self, reviews: List[Review]) -> str:
        """Format reviews for the prompt."""
        formatted = []
        for i, review in enumerate(reviews, 1):
            rating_str = f"{review.rating} stars" if review.rating else "N/A"
            product_str = f" | Product: {review.product_title}" if review.product_title else ""
            formatted.append(
                f"[Review {i}] Source: {review.source} | Rating: {rating_str}{product_str}\n"
                f"{review.review_text}\n"
            )
        return "\n---\n".join(formatted)
    
    def _parse_response(self, response_text: str) -> List[ExtractedPainPoint]:
        """Parse JSON response from Claude into ExtractedPainPoint objects."""
        # Extract JSON from response (handle markdown code blocks)
        json_text = self._extract_json(response_text)
        
        if not json_text:
            logger.warning("No JSON found in response")
            return []
        
        try:
            data = json.loads(json_text)
        except json.JSONDecodeError as e:
            logger.debug("Initial JSON parse failed, attempting fix: %s", e)
            # Try to fix common JSON issues
            json_text = self._fix_json(json_text)
            try:
                data = json.loads(json_text)
            except json.JSONDecodeError as e2:
                logger.warning("JSON parsing failed after fix attempt: %s", e2)
                return []
        
        if not isinstance(data, list):
            logger.warning("Response is not a JSON array")
            return []
        
        pain_points = []
        for item in data:
            try:
                pp = ExtractedPainPoint(
                    review_number=int(item.get("review_number", 0)),
                    pain_point_category=str(item.get("pain_point_category", "Unknown")),
                    verbatim_quote=str(item.get("verbatim_quote", "")),
                    emotional_intensity=str(item.get("emotional_intensity", "medium")).lower(),
                    implied_need=str(item.get("implied_need", "")),
                )
                if pp.verbatim_quote:  # Only add if we have a quote
                    pain_points.append(pp)
            except (ValueError, TypeError) as e:
                logger.debug("Skipping invalid pain point: %s", e)
                continue
        
        return pain_points
    
    def _extract_json(self, text: str) -> Optional[str]:
        """Extract JSON array from text, handling markdown code blocks."""
        # Try to find JSON in markdown code block
        code_block_pattern = r"```(?:json)?\s*([\s\S]*?)```"
        matches = re.findall(code_block_pattern, text)
        if matches:
            for match in matches:
                match = match.strip()
                if match.startswith("["):
                    return match
        
        # Try to find raw JSON array
        bracket_start = text.find("[")
        bracket_end = text.rfind("]")
        if bracket_start != -1 and bracket_end > bracket_start:
            return text[bracket_start:bracket_end + 1]
        
        return None
    
    def _fix_json(self, json_text: str) -> str:
        """Attempt to fix common JSON issues."""
        # Remove trailing commas before ] or }
        json_text = re.sub(r",\s*([}\]])", r"\1", json_text)
        
        # Fix unescaped quotes in strings (basic attempt)
        # This is a simplified fix - may not cover all cases
        
        return json_text
