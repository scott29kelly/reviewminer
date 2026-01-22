"""SQLite database operations for Review Miner."""

import sqlite3
from contextlib import contextmanager
from datetime import datetime
from pathlib import Path
from typing import Generator, Optional

from src.models import (
    JobStatus,
    PainPoint,
    PainPointStats,
    Review,
    ReviewStats,
    ScrapeJob,
)


SCHEMA = """
-- Reviews from all sources
CREATE TABLE IF NOT EXISTS reviews (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    source TEXT NOT NULL,
    source_url TEXT,
    product_title TEXT,
    product_url TEXT,
    author TEXT,
    rating INTEGER,
    review_text TEXT NOT NULL,
    review_date TEXT,
    scraped_at TEXT DEFAULT CURRENT_TIMESTAMP,
    processed BOOLEAN DEFAULT FALSE,
    UNIQUE(source, source_url, review_text)
);

-- Extracted pain points
CREATE TABLE IF NOT EXISTS pain_points (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    review_id INTEGER NOT NULL,
    category TEXT NOT NULL,
    verbatim_quote TEXT NOT NULL,
    emotional_intensity TEXT,
    implied_need TEXT,
    extracted_at TEXT DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (review_id) REFERENCES reviews(id)
);

-- Track scraping jobs
CREATE TABLE IF NOT EXISTS scrape_jobs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    source TEXT NOT NULL,
    query TEXT,
    status TEXT DEFAULT 'pending',
    reviews_found INTEGER DEFAULT 0,
    started_at TEXT,
    completed_at TEXT,
    error_message TEXT
);

-- Indexes for faster queries
CREATE INDEX IF NOT EXISTS idx_reviews_source ON reviews(source);
CREATE INDEX IF NOT EXISTS idx_reviews_processed ON reviews(processed);
CREATE INDEX IF NOT EXISTS idx_pain_points_category ON pain_points(category);
"""


class Database:
    """SQLite database manager for Review Miner."""
    
    def __init__(self, db_path: str = "data/review_miner.db"):
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
    
    @contextmanager
    def get_connection(self) -> Generator[sqlite3.Connection, None, None]:
        """Get a database connection with row factory."""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        try:
            yield conn
        finally:
            conn.close()
    
    def init_db(self) -> None:
        """Initialize the database with schema."""
        with self.get_connection() as conn:
            conn.executescript(SCHEMA)
            conn.commit()
    
    def reset_db(self) -> None:
        """Reset the database by dropping all tables and recreating."""
        with self.get_connection() as conn:
            conn.executescript("""
                DROP TABLE IF EXISTS pain_points;
                DROP TABLE IF EXISTS scrape_jobs;
                DROP TABLE IF EXISTS reviews;
            """)
            conn.executescript(SCHEMA)
            conn.commit()
    
    # ========== Review Operations ==========
    
    def insert_review(self, review: Review) -> int:
        """Insert a review and return its ID. Ignores duplicates."""
        with self.get_connection() as conn:
            cursor = conn.execute(
                """
                INSERT OR IGNORE INTO reviews 
                (source, source_url, product_title, product_url, author, rating, review_text, review_date, processed)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    review.source,
                    review.source_url,
                    review.product_title,
                    review.product_url,
                    review.author,
                    review.rating,
                    review.review_text,
                    review.review_date,
                    review.processed,
                ),
            )
            conn.commit()
            return cursor.lastrowid or 0
    
    def insert_reviews_batch(self, reviews: list[Review]) -> int:
        """Insert multiple reviews. Returns count of inserted rows."""
        with self.get_connection() as conn:
            cursor = conn.executemany(
                """
                INSERT OR IGNORE INTO reviews 
                (source, source_url, product_title, product_url, author, rating, review_text, review_date, processed)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                [
                    (
                        r.source,
                        r.source_url,
                        r.product_title,
                        r.product_url,
                        r.author,
                        r.rating,
                        r.review_text,
                        r.review_date,
                        r.processed,
                    )
                    for r in reviews
                ],
            )
            conn.commit()
            return cursor.rowcount
    
    def get_review(self, review_id: int) -> Optional[Review]:
        """Get a review by ID."""
        with self.get_connection() as conn:
            row = conn.execute(
                "SELECT * FROM reviews WHERE id = ?", (review_id,)
            ).fetchone()
            if row:
                return Review(**dict(row))
            return None
    
    def get_reviews(
        self,
        source: Optional[str] = None,
        processed: Optional[bool] = None,
        limit: Optional[int] = None,
    ) -> list[Review]:
        """Get reviews with optional filtering."""
        query = "SELECT * FROM reviews WHERE 1=1"
        params: list = []
        
        if source:
            query += " AND source = ?"
            params.append(source)
        
        if processed is not None:
            query += " AND processed = ?"
            params.append(processed)
        
        query += " ORDER BY id"
        
        if limit:
            query += " LIMIT ?"
            params.append(limit)
        
        with self.get_connection() as conn:
            rows = conn.execute(query, params).fetchall()
            return [Review(**dict(row)) for row in rows]
    
    def get_unprocessed_reviews(self, limit: Optional[int] = None) -> list[Review]:
        """Get reviews that haven't been processed yet."""
        return self.get_reviews(processed=False, limit=limit)
    
    def mark_reviews_processed(self, review_ids: list[int]) -> None:
        """Mark reviews as processed."""
        if not review_ids:
            return
        with self.get_connection() as conn:
            placeholders = ",".join("?" * len(review_ids))
            conn.execute(
                f"UPDATE reviews SET processed = TRUE WHERE id IN ({placeholders})",
                review_ids,
            )
            conn.commit()
    
    # ========== Pain Point Operations ==========
    
    def insert_pain_point(self, pain_point: PainPoint) -> int:
        """Insert a pain point and return its ID."""
        with self.get_connection() as conn:
            cursor = conn.execute(
                """
                INSERT INTO pain_points 
                (review_id, category, verbatim_quote, emotional_intensity, implied_need)
                VALUES (?, ?, ?, ?, ?)
                """,
                (
                    pain_point.review_id,
                    pain_point.category,
                    pain_point.verbatim_quote,
                    pain_point.emotional_intensity.value,
                    pain_point.implied_need,
                ),
            )
            conn.commit()
            return cursor.lastrowid or 0
    
    def insert_pain_points_batch(self, pain_points: list[PainPoint]) -> int:
        """Insert multiple pain points. Returns count of inserted rows."""
        with self.get_connection() as conn:
            cursor = conn.executemany(
                """
                INSERT INTO pain_points 
                (review_id, category, verbatim_quote, emotional_intensity, implied_need)
                VALUES (?, ?, ?, ?, ?)
                """,
                [
                    (
                        pp.review_id,
                        pp.category,
                        pp.verbatim_quote,
                        pp.emotional_intensity.value,
                        pp.implied_need,
                    )
                    for pp in pain_points
                ],
            )
            conn.commit()
            return cursor.rowcount
    
    def get_pain_points(
        self,
        category: Optional[str] = None,
        review_id: Optional[int] = None,
    ) -> list[PainPoint]:
        """Get pain points with optional filtering."""
        query = "SELECT * FROM pain_points WHERE 1=1"
        params: list = []
        
        if category:
            query += " AND category = ?"
            params.append(category)
        
        if review_id:
            query += " AND review_id = ?"
            params.append(review_id)
        
        query += " ORDER BY id"
        
        with self.get_connection() as conn:
            rows = conn.execute(query, params).fetchall()
            return [
                PainPoint(
                    id=row["id"],
                    review_id=row["review_id"],
                    category=row["category"],
                    verbatim_quote=row["verbatim_quote"],
                    emotional_intensity=row["emotional_intensity"],
                    implied_need=row["implied_need"],
                    extracted_at=row["extracted_at"],
                )
                for row in rows
            ]
    
    def get_all_pain_points_with_reviews(self) -> list[tuple[PainPoint, Review]]:
        """Get all pain points with their associated reviews."""
        query = """
            SELECT 
                p.id as p_id, p.review_id, p.category, p.verbatim_quote, 
                p.emotional_intensity, p.implied_need, p.extracted_at,
                r.id as r_id, r.source, r.source_url, r.product_title, 
                r.product_url, r.author, r.rating, r.review_text, 
                r.review_date, r.scraped_at, r.processed
            FROM pain_points p
            JOIN reviews r ON p.review_id = r.id
            ORDER BY p.category, p.id
        """
        with self.get_connection() as conn:
            rows = conn.execute(query).fetchall()
            results = []
            for row in rows:
                pain_point = PainPoint(
                    id=row["p_id"],
                    review_id=row["review_id"],
                    category=row["category"],
                    verbatim_quote=row["verbatim_quote"],
                    emotional_intensity=row["emotional_intensity"],
                    implied_need=row["implied_need"],
                    extracted_at=row["extracted_at"],
                )
                review = Review(
                    id=row["r_id"],
                    source=row["source"],
                    source_url=row["source_url"],
                    product_title=row["product_title"],
                    product_url=row["product_url"],
                    author=row["author"],
                    rating=row["rating"],
                    review_text=row["review_text"],
                    review_date=row["review_date"],
                    scraped_at=row["scraped_at"],
                    processed=row["processed"],
                )
                results.append((pain_point, review))
            return results
    
    # ========== Scrape Job Operations ==========
    
    def create_scrape_job(self, source: str, query: Optional[str] = None) -> int:
        """Create a new scrape job and return its ID."""
        with self.get_connection() as conn:
            cursor = conn.execute(
                """
                INSERT INTO scrape_jobs (source, query, status, started_at)
                VALUES (?, ?, ?, ?)
                """,
                (source, query, JobStatus.RUNNING.value, datetime.now().isoformat()),
            )
            conn.commit()
            return cursor.lastrowid or 0
    
    def update_scrape_job(
        self,
        job_id: int,
        status: Optional[JobStatus] = None,
        reviews_found: Optional[int] = None,
        error_message: Optional[str] = None,
    ) -> None:
        """Update a scrape job."""
        updates = []
        params: list = []
        
        if status:
            updates.append("status = ?")
            params.append(status.value)
            if status in (JobStatus.COMPLETED, JobStatus.FAILED):
                updates.append("completed_at = ?")
                params.append(datetime.now().isoformat())
        
        if reviews_found is not None:
            updates.append("reviews_found = ?")
            params.append(reviews_found)
        
        if error_message:
            updates.append("error_message = ?")
            params.append(error_message)
        
        if not updates:
            return
        
        params.append(job_id)
        with self.get_connection() as conn:
            conn.execute(
                f"UPDATE scrape_jobs SET {', '.join(updates)} WHERE id = ?",
                params,
            )
            conn.commit()
    
    # ========== Statistics ==========
    
    def get_review_stats(self) -> ReviewStats:
        """Get statistics about reviews."""
        with self.get_connection() as conn:
            total = conn.execute("SELECT COUNT(*) FROM reviews").fetchone()[0]
            
            by_source = {}
            for row in conn.execute(
                "SELECT source, COUNT(*) as count FROM reviews GROUP BY source"
            ).fetchall():
                by_source[row["source"]] = row["count"]
            
            processed = conn.execute(
                "SELECT COUNT(*) FROM reviews WHERE processed = TRUE"
            ).fetchone()[0]
            
            return ReviewStats(
                total_reviews=total,
                by_source=by_source,
                processed_count=processed,
                unprocessed_count=total - processed,
            )
    
    def get_pain_point_stats(self) -> PainPointStats:
        """Get statistics about pain points."""
        with self.get_connection() as conn:
            total = conn.execute("SELECT COUNT(*) FROM pain_points").fetchone()[0]
            
            by_category = {}
            for row in conn.execute(
                "SELECT category, COUNT(*) as count FROM pain_points GROUP BY category ORDER BY count DESC"
            ).fetchall():
                by_category[row["category"]] = row["count"]
            
            by_intensity = {}
            for row in conn.execute(
                "SELECT emotional_intensity, COUNT(*) as count FROM pain_points GROUP BY emotional_intensity"
            ).fetchall():
                by_intensity[row["emotional_intensity"]] = row["count"]
            
            return PainPointStats(
                total_pain_points=total,
                by_category=by_category,
                by_intensity=by_intensity,
            )


# Singleton instance
_db: Optional[Database] = None


def get_database(db_path: Optional[str] = None) -> Database:
    """Get the database singleton."""
    global _db
    if _db is None:
        from src.config import get_config
        path = db_path or get_config().config.database.path
        _db = Database(path)
    return _db
