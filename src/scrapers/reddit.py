"""Reddit scraper using PRAW (Python Reddit API Wrapper)."""

import asyncio
from typing import List, Optional

from tenacity import (
    retry,
    retry_if_exception_type,
    stop_after_attempt,
    wait_exponential,
)

from src.config import get_config
from src.exceptions import ConfigError, ScraperError
from src.logging_config import get_logger
from src.models import Review
from src.scrapers.base import BaseScraper


logger = get_logger(__name__)


# Pain keywords to search for in discussions
PAIN_KEYWORDS = [
    "disappointed",
    "waste of time",
    "didn't help",
    "overrated",
    "not worth",
    "struggled with",
    "couldn't finish",
    "expected more",
    "misleading",
    "frustrating",
    "useless",
    "waste of money",
]


class RedditScraper(BaseScraper):
    """Scrape reviews and discussions from Reddit using PRAW."""
    
    source_name = "reddit"
    
    def __init__(self):
        self.config = get_config()
        self._reddit = None
        logger.debug("Initialized RedditScraper")
    
    @property
    def reddit(self):
        """Lazy-load Reddit client."""
        if self._reddit is None:
            try:
                import praw
                import prawcore
            except ImportError:
                raise ImportError("PRAW is required for Reddit scraping. Install with: pip install praw")
            
            client_id = self.config.reddit_client_id
            client_secret = self.config.reddit_client_secret
            user_agent = self.config.reddit_user_agent
            
            if not client_id or not client_secret:
                raise ConfigError(
                    "Reddit API credentials required. "
                    "Set REDDIT_CLIENT_ID and REDDIT_CLIENT_SECRET in your .env file."
                )
            
            logger.debug("Initializing Reddit client")
            self._reddit = praw.Reddit(
                client_id=client_id,
                client_secret=client_secret,
                user_agent=user_agent,
            )
        return self._reddit
    
    def _get_prawcore_exceptions(self):
        """Get prawcore exception types for retry logic."""
        try:
            import prawcore
            return (
                prawcore.exceptions.ServerError,
                prawcore.exceptions.RequestException,
                prawcore.exceptions.ResponseException,
            )
        except ImportError:
            return (Exception,)
    
    async def search(self, query: str, max_results: int = 50) -> List[str]:
        """Search for Reddit posts matching query."""
        logger.info("Searching Reddit for: %s", query)
        
        # Reddit search returns submissions, not URLs
        # This method returns submission IDs
        try:
            subreddit = self.reddit.subreddit("all")
            submissions = []
            
            for submission in subreddit.search(query, limit=max_results):
                submissions.append(submission.id)
            
            logger.info("Found %d submissions", len(submissions))
            return submissions
        except Exception as e:
            logger.error("Reddit search failed: %s", e)
            return []
    
    async def scrape_reviews(
        self,
        url: str,
        max_reviews: int = 100,
        min_rating: int = 1,
        max_rating: int = 3,
    ) -> List[Review]:
        """Scrape a single Reddit post and its comments."""
        logger.debug("Scraping Reddit post: %s", url)
        
        # For Reddit, URL can be a post URL or submission ID
        try:
            if url.startswith("http"):
                submission = self.reddit.submission(url=url)
            else:
                submission = self.reddit.submission(id=url)
            
            reviews = self._extract_reviews_from_submission(submission, max_reviews)
            logger.debug("Extracted %d reviews from submission", len(reviews))
            return reviews
        except Exception as e:
            logger.error("Failed to scrape submission: %s", e)
            return []
    
    async def search_and_scrape(
        self,
        query: str,
        subreddits: Optional[List[str]] = None,
        max_posts: int = 50,
    ) -> List[Review]:
        """
        Search Reddit for discussions about a topic and extract pain points.
        
        Args:
            query: Search query (e.g., book title)
            subreddits: List of subreddits to search (default from config)
            max_posts: Maximum posts to search
        """
        logger.info("Starting Reddit search and scrape for: %s", query)
        
        if subreddits is None:
            subreddits = self.config.config.scraping.reddit.subreddits
        
        pain_keywords = self.config.config.scraping.reddit.pain_keywords
        
        all_reviews = []
        subreddit_str = "+".join(subreddits)
        logger.debug("Searching in subreddits: %s", subreddit_str)
        
        try:
            subreddit = self.reddit.subreddit(subreddit_str)
        except Exception as e:
            logger.error("Failed to access subreddits: %s", e)
            raise ScraperError(f"Failed to access subreddits: {e}") from e
        
        # Search with pain keywords
        search_queries = [f'"{query}"']
        for keyword in pain_keywords[:3]:  # Limit to avoid too many searches
            search_queries.append(f'"{query}" {keyword}')
        
        seen_ids = set()
        
        for search_query in search_queries:
            logger.debug("Searching with query: %s", search_query)
            try:
                results = list(subreddit.search(search_query, limit=max_posts // len(search_queries)))
                logger.debug("Found %d results for query", len(results))
                
                for submission in results:
                    if submission.id in seen_ids:
                        continue
                    seen_ids.add(submission.id)
                    
                    reviews = self._extract_reviews_from_submission(submission)
                    all_reviews.extend(reviews)
                    
                    # Small delay to be nice to API
                    await asyncio.sleep(0.1)
                    
            except Exception as e:
                logger.warning("Search query failed: %s - %s", search_query, e)
                continue
        
        logger.info("Total reviews collected: %d", len(all_reviews))
        return all_reviews
    
    def _extract_reviews_from_submission(
        self,
        submission,
        max_comments: int = 50,
    ) -> List[Review]:
        """Extract reviews from a Reddit submission and its comments."""
        reviews = []
        
        try:
            # Extract from post body if it has content
            if submission.selftext and len(submission.selftext) >= 50:
                reviews.append(Review(
                    source=self.source_name,
                    source_url=f"https://reddit.com{submission.permalink}",
                    product_title=submission.title,
                    author=str(submission.author) if submission.author else None,
                    rating=None,  # Reddit doesn't have ratings
                    review_text=submission.selftext,
                    review_date=None,
                ))
            
            # Extract from comments
            submission.comments.replace_more(limit=0)  # Don't load "more comments"
            
            for comment in submission.comments.list()[:max_comments]:
                if hasattr(comment, "body") and len(comment.body) >= 50:
                    # Skip bot comments and deleted content
                    if comment.body in ("[deleted]", "[removed]"):
                        continue
                    if comment.author and str(comment.author).lower() in ("automoderator", "bot"):
                        continue
                    
                    reviews.append(Review(
                        source=self.source_name,
                        source_url=f"https://reddit.com{comment.permalink}",
                        product_title=submission.title,
                        author=str(comment.author) if comment.author else None,
                        rating=None,
                        review_text=comment.body,
                        review_date=None,
                    ))
        except Exception as e:
            logger.warning("Error extracting from submission: %s", e)
        
        return reviews
