"""Pydantic data models for Review Miner."""

from datetime import datetime
from enum import Enum
from typing import Optional

from pydantic import BaseModel, Field


class JobStatus(str, Enum):
    """Status of a scrape job."""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"


class EmotionalIntensity(str, Enum):
    """Emotional intensity level of a pain point."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


class Review(BaseModel):
    """A review scraped from a source."""
    id: Optional[int] = None
    source: str  # 'amazon', 'goodreads', 'reddit', etc.
    source_url: Optional[str] = None
    product_title: Optional[str] = None
    product_url: Optional[str] = None
    author: Optional[str] = None
    rating: Optional[int] = Field(None, ge=1, le=5)  # 1-5 stars (NULL for Reddit)
    review_text: str
    review_date: Optional[str] = None
    scraped_at: Optional[datetime] = None
    processed: bool = False

    class Config:
        from_attributes = True


class PainPoint(BaseModel):
    """An extracted pain point from a review."""
    id: Optional[int] = None
    review_id: int
    category: str  # e.g., "Too theoretical", "Outdated advice"
    verbatim_quote: str
    emotional_intensity: EmotionalIntensity = EmotionalIntensity.MEDIUM
    implied_need: Optional[str] = None  # What they actually wanted
    extracted_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class ScrapeJob(BaseModel):
    """A scraping job record."""
    id: Optional[int] = None
    source: str
    query: Optional[str] = None  # Search term or URL
    status: JobStatus = JobStatus.PENDING
    reviews_found: int = 0
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    error_message: Optional[str] = None

    class Config:
        from_attributes = True


class ExtractedPainPoint(BaseModel):
    """Pain point as extracted from Claude API response."""
    review_number: int
    pain_point_category: str
    verbatim_quote: str
    emotional_intensity: str
    implied_need: str


class AnalysisResult(BaseModel):
    """Result of analyzing a batch of reviews."""
    pain_points: list[ExtractedPainPoint] = Field(default_factory=list)
    reviews_processed: int = 0
    errors: list[str] = Field(default_factory=list)


class ReviewStats(BaseModel):
    """Statistics about reviews in the database."""
    total_reviews: int = 0
    by_source: dict[str, int] = Field(default_factory=dict)
    processed_count: int = 0
    unprocessed_count: int = 0


class PainPointStats(BaseModel):
    """Statistics about pain points in the database."""
    total_pain_points: int = 0
    by_category: dict[str, int] = Field(default_factory=dict)
    by_intensity: dict[str, int] = Field(default_factory=dict)
