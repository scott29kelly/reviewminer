"""
Pain Points API Router
"""
import io
import csv
import json
from typing import Optional

from fastapi import APIRouter, Query, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from src.database import get_database
from src.exporter import Exporter


router = APIRouter()


class PainPointResponse(BaseModel):
    id: int
    review_id: int
    category: str
    verbatim_quote: str
    emotional_intensity: str
    implied_need: Optional[str] = None
    extracted_at: Optional[str] = None
    # Include review info
    source: Optional[str] = None
    product_title: Optional[str] = None
    rating: Optional[int] = None


class PainPointsListResponse(BaseModel):
    pain_points: list[PainPointResponse]
    total: int
    page: int
    page_size: int
    total_pages: int


class CategoryCount(BaseModel):
    category: str
    count: int


@router.get("", response_model=PainPointsListResponse)
async def get_pain_points(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    category: Optional[str] = None,
    intensity: Optional[str] = Query(None, regex="^(low|medium|high)$"),
    source: Optional[str] = None,
    search: Optional[str] = None,
    sort_by: str = Query("extracted_at", regex="^(extracted_at|category|emotional_intensity)$"),
    sort_order: str = Query("desc", regex="^(asc|desc)$"),
):
    """Get paginated list of pain points with filtering."""
    db = get_database()
    
    # Get all pain points with their reviews
    all_pain_points = db.get_all_pain_points_with_reviews()
    
    # Apply filters
    filtered = []
    for pp, review in all_pain_points:
        # Category filter
        if category and pp.category != category:
            continue
        
        # Intensity filter
        intensity_value = pp.emotional_intensity.value if pp.emotional_intensity else "medium"
        if intensity and intensity_value != intensity:
            continue
        
        # Source filter
        if source and review.source != source:
            continue
        
        # Search filter
        if search:
            search_lower = search.lower()
            if not (
                search_lower in pp.verbatim_quote.lower()
                or search_lower in pp.category.lower()
                or (pp.implied_need and search_lower in pp.implied_need.lower())
            ):
                continue
        
        filtered.append((pp, review))
    
    # Sort
    def get_sort_key(item):
        pp, review = item
        if sort_by == "category":
            return pp.category
        elif sort_by == "emotional_intensity":
            return pp.emotional_intensity.value if pp.emotional_intensity else "medium"
        else:  # extracted_at
            return pp.extracted_at.isoformat() if pp.extracted_at else ""
    
    filtered.sort(key=get_sort_key, reverse=(sort_order == "desc"))
    
    # Paginate
    total = len(filtered)
    total_pages = (total + page_size - 1) // page_size
    start = (page - 1) * page_size
    end = start + page_size
    page_items = filtered[start:end]
    
    return PainPointsListResponse(
        pain_points=[
            PainPointResponse(
                id=pp.id,
                review_id=pp.review_id,
                category=pp.category,
                verbatim_quote=pp.verbatim_quote,
                emotional_intensity=pp.emotional_intensity.value if pp.emotional_intensity else "medium",
                implied_need=pp.implied_need,
                extracted_at=pp.extracted_at.isoformat() if pp.extracted_at else None,
                source=review.source,
                product_title=review.product_title,
                rating=review.rating,
            )
            for pp, review in page_items
        ],
        total=total,
        page=page,
        page_size=page_size,
        total_pages=total_pages,
    )


@router.get("/categories", response_model=list[CategoryCount])
async def get_categories():
    """Get all categories with counts."""
    db = get_database()
    stats = db.get_pain_point_stats()
    
    return [
        CategoryCount(category=cat, count=count)
        for cat, count in sorted(stats.by_category.items(), key=lambda x: x[1], reverse=True)
    ]


@router.get("/export")
async def export_pain_points(
    format: str = Query("csv", regex="^(csv|json|markdown|md)$"),
    category: Optional[str] = None,
):
    """Export pain points to file."""
    db = get_database()
    all_pain_points = db.get_all_pain_points_with_reviews()
    
    # Filter by category if specified
    if category:
        all_pain_points = [(pp, r) for pp, r in all_pain_points if pp.category == category]
    
    if format == "json":
        data = [
            {
                "category": pp.category,
                "verbatim_quote": pp.verbatim_quote,
                "emotional_intensity": pp.emotional_intensity.value if pp.emotional_intensity else "medium",
                "implied_need": pp.implied_need,
                "source": {
                    "platform": review.source,
                    "product_title": review.product_title,
                    "rating": review.rating,
                    "review_date": review.review_date,
                },
            }
            for pp, review in all_pain_points
        ]
        content = json.dumps(data, indent=2)
        return StreamingResponse(
            io.BytesIO(content.encode()),
            media_type="application/json",
            headers={"Content-Disposition": "attachment; filename=pain_points.json"},
        )
    
    elif format == "csv":
        output = io.StringIO()
        writer = csv.writer(output)
        writer.writerow(["category", "verbatim_quote", "emotional_intensity", "implied_need", "source", "product_title", "rating"])
        
        for pp, review in all_pain_points:
            writer.writerow([
                pp.category,
                pp.verbatim_quote,
                pp.emotional_intensity.value if pp.emotional_intensity else "medium",
                pp.implied_need or "",
                review.source,
                review.product_title or "",
                review.rating or "",
            ])
        
        content = output.getvalue()
        return StreamingResponse(
            io.BytesIO(content.encode()),
            media_type="text/csv",
            headers={"Content-Disposition": "attachment; filename=pain_points.csv"},
        )
    
    else:  # markdown
        # Group by category
        by_category = {}
        for pp, review in all_pain_points:
            if pp.category not in by_category:
                by_category[pp.category] = []
            by_category[pp.category].append((pp, review))
        
        lines = ["# Pain Points Report\n"]
        lines.append(f"**Total Pain Points:** {len(all_pain_points)}\n")
        lines.append("---\n")
        
        for cat, items in sorted(by_category.items(), key=lambda x: len(x[1]), reverse=True):
            lines.append(f"## {cat} ({len(items)})\n")
            for pp, review in items:
                intensity_emoji = {"high": "🔴", "medium": "🟡", "low": "🟢"}.get(
                    pp.emotional_intensity.value if pp.emotional_intensity else "medium", "🟡"
                )
                lines.append(f"- {intensity_emoji} \"{pp.verbatim_quote}\"")
                if review.product_title:
                    lines.append(f"  - Source: {review.product_title} ({review.source})")
                if pp.implied_need:
                    lines.append(f"  - Implied need: {pp.implied_need}")
                lines.append("")
        
        content = "\n".join(lines)
        return StreamingResponse(
            io.BytesIO(content.encode()),
            media_type="text/markdown",
            headers={"Content-Disposition": "attachment; filename=pain_points.md"},
        )
