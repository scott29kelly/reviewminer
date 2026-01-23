"""
Analysis API Router
"""
import asyncio
from typing import Optional

from fastapi import APIRouter, Query, HTTPException, BackgroundTasks
from pydantic import BaseModel

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from src.database import get_database
from src.analyzer import PainPointAnalyzer
from src.models import PainPoint
from api.websocket import job_manager


router = APIRouter()


class AnalyzeRequest(BaseModel):
    source: Optional[str] = None
    unprocessed_only: bool = True
    batch_size: int = 20


class AnalyzeResponse(BaseModel):
    message: str
    reviews_queued: int
    job_id: Optional[int] = None


# Track running analysis
analysis_running = False


async def run_analysis(source: Optional[str], unprocessed_only: bool, batch_size: int):
    """Run analysis in the background."""
    global analysis_running
    
    try:
        db = get_database()
        analyzer = PainPointAnalyzer()
        
        # Get reviews to analyze
        if unprocessed_only:
            reviews = db.get_unprocessed_reviews(limit=None)
        else:
            reviews = db.get_reviews(source=source, limit=None)
        
        if not reviews:
            await job_manager.broadcast(-1, {"type": "analysis", "status": "completed", "message": "No reviews to analyze"})
            return
        
        total = len(reviews)
        await job_manager.broadcast(-1, {"type": "analysis", "status": "running", "message": f"Analyzing {total} reviews..."})
        
        # Analyze in batches
        for i in range(0, total, batch_size):
            batch = reviews[i:i + batch_size]
            
            await job_manager.broadcast(-1, {
                "type": "analysis",
                "status": "running",
                "progress": i / total * 100,
                "message": f"Processing batch {i // batch_size + 1}...",
            })
            
            # Run analysis
            result = await asyncio.to_thread(analyzer.analyze_with_result, batch)
            
            # Save pain points
            pain_points = []
            for extracted in result.pain_points:
                if extracted.review_number <= len(batch):
                    review = batch[extracted.review_number - 1]
                    from src.models import EmotionalIntensity
                    pain_points.append(PainPoint(
                        review_id=review.id,
                        category=extracted.pain_point_category,
                        verbatim_quote=extracted.verbatim_quote,
                        emotional_intensity=EmotionalIntensity(extracted.emotional_intensity.lower()),
                        implied_need=extracted.implied_need,
                    ))
            
            if pain_points:
                db.insert_pain_points_batch(pain_points)
            
            # Mark reviews as processed
            review_ids = [r.id for r in batch]
            db.mark_reviews_processed(review_ids)
        
        stats = db.get_pain_point_stats()
        await job_manager.broadcast(-1, {
            "type": "analysis",
            "status": "completed",
            "message": f"Analysis complete. {stats.total_pain_points} total pain points.",
        })
    
    except Exception as e:
        await job_manager.broadcast(-1, {
            "type": "analysis",
            "status": "failed",
            "error": str(e),
            "message": f"Analysis failed: {str(e)}",
        })
    
    finally:
        analysis_running = False


@router.post("", response_model=AnalyzeResponse)
async def start_analysis(request: AnalyzeRequest, background_tasks: BackgroundTasks):
    """Start analysis of reviews."""
    global analysis_running
    
    if analysis_running:
        raise HTTPException(status_code=409, detail="Analysis is already running")
    
    db = get_database()
    
    # Count reviews to analyze
    if request.unprocessed_only:
        reviews = db.get_unprocessed_reviews(limit=None)
    else:
        reviews = db.get_reviews(source=request.source, limit=None)
    
    if not reviews:
        return AnalyzeResponse(message="No reviews to analyze", reviews_queued=0)
    
    analysis_running = True
    
    # Start background analysis
    asyncio.create_task(run_analysis(request.source, request.unprocessed_only, request.batch_size))
    
    return AnalyzeResponse(
        message=f"Analysis started for {len(reviews)} reviews",
        reviews_queued=len(reviews),
    )


@router.get("/status")
async def get_analysis_status():
    """Get current analysis status."""
    return {"running": analysis_running}
