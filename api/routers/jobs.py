"""
Scrape Jobs API Router
"""
import asyncio
from typing import Optional
from datetime import datetime
from enum import Enum

from fastapi import APIRouter, Query, HTTPException, BackgroundTasks
from pydantic import BaseModel

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from src.database import get_database
from src.models import JobStatus, ScrapeJob
from api.websocket import job_manager


router = APIRouter()


class JobSource(str, Enum):
    amazon = "amazon"
    goodreads = "goodreads"
    reddit = "reddit"
    librarything = "librarything"


class CreateJobRequest(BaseModel):
    source: JobSource
    query: str
    max_reviews: int = 50
    max_products: int = 10  # For Amazon
    subreddits: Optional[str] = None  # For Reddit


class JobResponse(BaseModel):
    id: int
    source: str
    query: Optional[str] = None
    status: str
    reviews_found: int
    started_at: Optional[str] = None
    completed_at: Optional[str] = None
    error_message: Optional[str] = None


class JobsListResponse(BaseModel):
    jobs: list[JobResponse]
    total: int


# Store for running job tasks
running_jobs: dict[int, asyncio.Task] = {}


async def run_scrape_job(job_id: int, source: str, query: str, options: dict):
    """Run a scrape job in the background."""
    db = get_database()
    
    try:
        await job_manager.broadcast(job_id, {"status": "running", "message": "Starting scrape..."})
        
        reviews = []
        
        if source == "amazon":
            from src.scrapers import get_amazon_scraper
            scraper = get_amazon_scraper()()
            reviews = await asyncio.to_thread(
                scraper.search_and_scrape,
                query,
                max_products=options.get("max_products", 10),
                max_reviews_per_product=options.get("max_reviews", 50),
            )
        
        elif source == "goodreads":
            from src.scrapers import get_goodreads_scraper
            scraper = get_goodreads_scraper()()
            reviews = await asyncio.to_thread(
                scraper.scrape_book_reviews,
                query,
                max_reviews=options.get("max_reviews", 100),
            )
        
        elif source == "reddit":
            from src.scrapers import get_reddit_scraper
            scraper = get_reddit_scraper()()
            subreddits = options.get("subreddits", "books,suggestmeabook").split(",")
            reviews = await scraper.search_and_scrape(
                query,
                subreddits=subreddits,
                max_posts=options.get("max_reviews", 50),
            )
        
        elif source == "librarything":
            from src.scrapers import get_librarything_scraper
            scraper = get_librarything_scraper()()
            reviews = await asyncio.to_thread(
                scraper.scrape_work_reviews,
                query,
                max_reviews=options.get("max_reviews", 100),
            )
        
        # Insert reviews
        if reviews:
            count = db.insert_reviews_batch(reviews)
            db.update_scrape_job(job_id, status=JobStatus.COMPLETED, reviews_found=count)
            await job_manager.broadcast(job_id, {
                "status": "completed",
                "reviews_found": count,
                "message": f"Successfully scraped {count} reviews",
            })
        else:
            db.update_scrape_job(job_id, status=JobStatus.COMPLETED, reviews_found=0)
            await job_manager.broadcast(job_id, {
                "status": "completed",
                "reviews_found": 0,
                "message": "No reviews found",
            })
    
    except Exception as e:
        error_msg = str(e)
        db.update_scrape_job(job_id, status=JobStatus.FAILED, error_message=error_msg)
        await job_manager.broadcast(job_id, {
            "status": "failed",
            "error": error_msg,
            "message": f"Scrape failed: {error_msg}",
        })
    
    finally:
        # Clean up
        if job_id in running_jobs:
            del running_jobs[job_id]


@router.get("", response_model=JobsListResponse)
async def get_jobs(
    status: Optional[str] = Query(None, regex="^(pending|running|completed|failed)$"),
    limit: int = Query(50, ge=1, le=200),
):
    """Get list of scrape jobs."""
    db = get_database()
    
    with db.get_connection() as conn:
        if status:
            cursor = conn.execute(
                "SELECT * FROM scrape_jobs WHERE status = ? ORDER BY started_at DESC LIMIT ?",
                (status, limit),
            )
        else:
            cursor = conn.execute(
                "SELECT * FROM scrape_jobs ORDER BY started_at DESC LIMIT ?",
                (limit,),
            )
        
        rows = cursor.fetchall()
    
    jobs = []
    for row in rows:
        jobs.append(JobResponse(
            id=row["id"],
            source=row["source"],
            query=row["query"],
            status=row["status"],
            reviews_found=row["reviews_found"],
            started_at=row["started_at"],
            completed_at=row["completed_at"],
            error_message=row["error_message"],
        ))
    
    return JobsListResponse(jobs=jobs, total=len(jobs))


@router.post("", response_model=JobResponse)
async def create_job(request: CreateJobRequest, background_tasks: BackgroundTasks):
    """Create and start a new scrape job."""
    db = get_database()
    
    # Create job record
    job_id = db.create_scrape_job(source=request.source.value, query=request.query)
    
    # Get the created job
    with db.get_connection() as conn:
        cursor = conn.execute("SELECT * FROM scrape_jobs WHERE id = ?", (job_id,))
        row = cursor.fetchone()
    
    # Start background task
    options = {
        "max_reviews": request.max_reviews,
        "max_products": request.max_products,
        "subreddits": request.subreddits,
    }
    
    task = asyncio.create_task(run_scrape_job(job_id, request.source.value, request.query, options))
    running_jobs[job_id] = task
    
    return JobResponse(
        id=row["id"],
        source=row["source"],
        query=row["query"],
        status=row["status"],
        reviews_found=row["reviews_found"],
        started_at=row["started_at"],
        completed_at=row["completed_at"],
        error_message=row["error_message"],
    )


@router.delete("/{job_id}")
async def cancel_job(job_id: int):
    """Cancel a running job."""
    db = get_database()
    
    # Check if job exists
    with db.get_connection() as conn:
        cursor = conn.execute("SELECT * FROM scrape_jobs WHERE id = ?", (job_id,))
        row = cursor.fetchone()
    
    if not row:
        raise HTTPException(status_code=404, detail="Job not found")
    
    if row["status"] not in ("pending", "running"):
        raise HTTPException(status_code=400, detail="Job is not running")
    
    # Cancel the task if it exists
    if job_id in running_jobs:
        running_jobs[job_id].cancel()
        del running_jobs[job_id]
    
    # Update status
    db.update_scrape_job(job_id, status=JobStatus.FAILED, error_message="Cancelled by user")
    
    await job_manager.broadcast(job_id, {"status": "cancelled", "message": "Job cancelled"})
    
    return {"message": "Job cancelled", "id": job_id}
