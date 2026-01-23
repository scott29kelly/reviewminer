"""
Statistics API Router
"""
from fastapi import APIRouter
from pydantic import BaseModel

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from src.database import get_database


router = APIRouter()


class ReviewStatsResponse(BaseModel):
    total_reviews: int
    processed_count: int
    unprocessed_count: int
    by_source: dict[str, int]


class PainPointStatsResponse(BaseModel):
    total_pain_points: int
    by_category: dict[str, int]
    by_intensity: dict[str, int]


class DashboardStats(BaseModel):
    reviews: ReviewStatsResponse
    pain_points: PainPointStatsResponse
    recent_reviews: list[dict]
    recent_pain_points: list[dict]


@router.get("/reviews", response_model=ReviewStatsResponse)
async def get_review_stats():
    """Get review statistics."""
    db = get_database()
    stats = db.get_review_stats()
    
    return ReviewStatsResponse(
        total_reviews=stats.total_reviews,
        processed_count=stats.processed_count,
        unprocessed_count=stats.unprocessed_count,
        by_source=stats.by_source,
    )


@router.get("/pain-points", response_model=PainPointStatsResponse)
async def get_pain_point_stats():
    """Get pain point statistics."""
    db = get_database()
    stats = db.get_pain_point_stats()
    
    return PainPointStatsResponse(
        total_pain_points=stats.total_pain_points,
        by_category=stats.by_category,
        by_intensity=stats.by_intensity,
    )


@router.get("/dashboard", response_model=DashboardStats)
async def get_dashboard_stats():
    """Get all dashboard statistics."""
    db = get_database()
    
    review_stats = db.get_review_stats()
    pain_point_stats = db.get_pain_point_stats()
    
    # Get recent reviews
    recent_reviews = db.get_reviews(limit=5)
    recent_reviews_data = [
        {
            "id": r.id,
            "source": r.source,
            "product_title": r.product_title,
            "rating": r.rating,
            "review_text": r.review_text[:150] + "..." if len(r.review_text) > 150 else r.review_text,
            "scraped_at": r.scraped_at.isoformat() if r.scraped_at else None,
        }
        for r in recent_reviews
    ]
    
    # Get recent pain points
    all_pain_points = db.get_all_pain_points_with_reviews()
    recent_pain_points_data = [
        {
            "id": pp.id,
            "category": pp.category,
            "verbatim_quote": pp.verbatim_quote[:100] + "..." if len(pp.verbatim_quote) > 100 else pp.verbatim_quote,
            "emotional_intensity": pp.emotional_intensity.value if pp.emotional_intensity else "medium",
            "source": review.source,
        }
        for pp, review in all_pain_points[:5]
    ]
    
    return DashboardStats(
        reviews=ReviewStatsResponse(
            total_reviews=review_stats.total_reviews,
            processed_count=review_stats.processed_count,
            unprocessed_count=review_stats.unprocessed_count,
            by_source=review_stats.by_source,
        ),
        pain_points=PainPointStatsResponse(
            total_pain_points=pain_point_stats.total_pain_points,
            by_category=pain_point_stats.by_category,
            by_intensity=pain_point_stats.by_intensity,
        ),
        recent_reviews=recent_reviews_data,
        recent_pain_points=recent_pain_points_data,
    )
