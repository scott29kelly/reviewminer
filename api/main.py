"""
ReviewMiner FastAPI Backend
"""
import sys
from pathlib import Path
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from api.routers import reviews, pain_points, jobs, stats, analysis
from api.websocket import router as websocket_router
from src.database import get_database


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Initialize database on startup."""
    db = get_database()
    db.init_db()
    yield


app = FastAPI(
    title="ReviewMiner API",
    description="API for scraping and analyzing book reviews",
    version="1.0.0",
    lifespan=lifespan,
)

# CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://localhost:3001",
        "http://127.0.0.1:3000",
        "http://127.0.0.1:3001",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(reviews.router, prefix="/api/reviews", tags=["Reviews"])
app.include_router(pain_points.router, prefix="/api/pain-points", tags=["Pain Points"])
app.include_router(jobs.router, prefix="/api/jobs", tags=["Jobs"])
app.include_router(stats.router, prefix="/api/stats", tags=["Statistics"])
app.include_router(analysis.router, prefix="/api/analysis", tags=["Analysis"])
app.include_router(websocket_router, prefix="/api/ws", tags=["WebSocket"])


@app.get("/api/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy", "service": "reviewminer-api"}
