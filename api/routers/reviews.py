"""
Reviews API Router
"""
import io
import csv
import json
from typing import Optional
from datetime import datetime

from fastapi import APIRouter, Query, HTTPException, UploadFile, File
from pydantic import BaseModel

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from src.database import get_database
from src.models import Review


router = APIRouter()


class ReviewResponse(BaseModel):
    id: int
    source: str
    source_url: Optional[str] = None
    product_title: Optional[str] = None
    product_url: Optional[str] = None
    author: Optional[str] = None
    rating: Optional[int] = None
    review_text: str
    review_date: Optional[str] = None
    scraped_at: Optional[str] = None
    processed: bool


class ReviewsListResponse(BaseModel):
    reviews: list[ReviewResponse]
    total: int
    page: int
    page_size: int
    total_pages: int


class ReviewWithPainPoints(ReviewResponse):
    pain_points: list[dict]


@router.get("", response_model=ReviewsListResponse)
async def get_reviews(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    source: Optional[str] = None,
    processed: Optional[bool] = None,
    rating_min: Optional[int] = Query(None, ge=1, le=5),
    rating_max: Optional[int] = Query(None, ge=1, le=5),
    search: Optional[str] = None,
    sort_by: str = Query("scraped_at", regex="^(scraped_at|rating|source|review_date)$"),
    sort_order: str = Query("desc", regex="^(asc|desc)$"),
):
    """Get paginated list of reviews with filtering."""
    db = get_database()
    
    # Get all reviews (we'll filter in memory for now - can optimize with raw SQL later)
    all_reviews = db.get_reviews(source=source, processed=processed, limit=None)
    
    # Apply additional filters
    filtered = all_reviews
    
    if rating_min is not None:
        filtered = [r for r in filtered if r.rating is not None and r.rating >= rating_min]
    
    if rating_max is not None:
        filtered = [r for r in filtered if r.rating is not None and r.rating <= rating_max]
    
    if search:
        search_lower = search.lower()
        filtered = [
            r for r in filtered 
            if search_lower in r.review_text.lower() 
            or (r.product_title and search_lower in r.product_title.lower())
            or (r.author and search_lower in r.author.lower())
        ]
    
    # Sort
    def get_sort_key(r: Review):
        if sort_by == "rating":
            return r.rating or 0
        elif sort_by == "source":
            return r.source
        elif sort_by == "review_date":
            return r.review_date or ""
        else:  # scraped_at
            return r.scraped_at.isoformat() if r.scraped_at else ""
    
    filtered.sort(key=get_sort_key, reverse=(sort_order == "desc"))
    
    # Paginate
    total = len(filtered)
    total_pages = (total + page_size - 1) // page_size
    start = (page - 1) * page_size
    end = start + page_size
    page_reviews = filtered[start:end]
    
    return ReviewsListResponse(
        reviews=[
            ReviewResponse(
                id=r.id,
                source=r.source,
                source_url=r.source_url,
                product_title=r.product_title,
                product_url=r.product_url,
                author=r.author,
                rating=r.rating,
                review_text=r.review_text,
                review_date=r.review_date,
                scraped_at=r.scraped_at.isoformat() if r.scraped_at else None,
                processed=r.processed,
            )
            for r in page_reviews
        ],
        total=total,
        page=page,
        page_size=page_size,
        total_pages=total_pages,
    )


@router.get("/{review_id}", response_model=ReviewWithPainPoints)
async def get_review(review_id: int):
    """Get a single review with its pain points."""
    db = get_database()
    review = db.get_review(review_id)
    
    if not review:
        raise HTTPException(status_code=404, detail="Review not found")
    
    # Get pain points for this review
    pain_points = db.get_pain_points(review_id=review_id)
    
    return ReviewWithPainPoints(
        id=review.id,
        source=review.source,
        source_url=review.source_url,
        product_title=review.product_title,
        product_url=review.product_url,
        author=review.author,
        rating=review.rating,
        review_text=review.review_text,
        review_date=review.review_date,
        scraped_at=review.scraped_at.isoformat() if review.scraped_at else None,
        processed=review.processed,
        pain_points=[
            {
                "id": pp.id,
                "category": pp.category,
                "verbatim_quote": pp.verbatim_quote,
                "emotional_intensity": pp.emotional_intensity.value if pp.emotional_intensity else "medium",
                "implied_need": pp.implied_need,
            }
            for pp in pain_points
        ],
    )


@router.delete("/{review_id}")
async def delete_review(review_id: int):
    """Delete a review."""
    db = get_database()
    review = db.get_review(review_id)
    
    if not review:
        raise HTTPException(status_code=404, detail="Review not found")
    
    # Delete using raw SQL
    with db.get_connection() as conn:
        # Delete associated pain points first
        conn.execute("DELETE FROM pain_points WHERE review_id = ?", (review_id,))
        conn.execute("DELETE FROM reviews WHERE id = ?", (review_id,))
        conn.commit()
    
    return {"message": "Review deleted", "id": review_id}


@router.post("/import")
async def import_reviews(
    file: UploadFile = File(...),
    source: str = Query("manual", description="Source name for imported reviews"),
):
    """Import reviews from CSV or JSON file."""
    db = get_database()
    
    content = await file.read()
    filename = file.filename.lower()
    
    reviews_to_import = []
    
    try:
        if filename.endswith(".json"):
            data = json.loads(content.decode("utf-8"))
            if isinstance(data, list):
                for item in data:
                    reviews_to_import.append(
                        Review(
                            source=source,
                            review_text=item.get("review_text", item.get("text", "")),
                            product_title=item.get("product_title", item.get("title")),
                            author=item.get("author"),
                            rating=item.get("rating"),
                            review_date=item.get("review_date", item.get("date")),
                        )
                    )
        elif filename.endswith(".csv"):
            text = content.decode("utf-8")
            reader = csv.DictReader(io.StringIO(text))
            for row in reader:
                review_text = row.get("review_text") or row.get("text") or row.get("content")
                if review_text:
                    reviews_to_import.append(
                        Review(
                            source=source,
                            review_text=review_text,
                            product_title=row.get("product_title") or row.get("title"),
                            author=row.get("author"),
                            rating=int(row["rating"]) if row.get("rating") else None,
                            review_date=row.get("review_date") or row.get("date"),
                        )
                    )
        else:
            raise HTTPException(status_code=400, detail="Unsupported file format. Use CSV or JSON.")
        
        if not reviews_to_import:
            raise HTTPException(status_code=400, detail="No valid reviews found in file")
        
        count = db.insert_reviews_batch(reviews_to_import)
        
        return {"message": f"Imported {count} reviews", "count": count}
    
    except json.JSONDecodeError:
        raise HTTPException(status_code=400, detail="Invalid JSON file")
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/bulk-delete")
async def bulk_delete_reviews(review_ids: list[int]):
    """Delete multiple reviews."""
    db = get_database()
    
    with db.get_connection() as conn:
        for review_id in review_ids:
            conn.execute("DELETE FROM pain_points WHERE review_id = ?", (review_id,))
            conn.execute("DELETE FROM reviews WHERE id = ?", (review_id,))
        conn.commit()
    
    return {"message": f"Deleted {len(review_ids)} reviews", "count": len(review_ids)}
