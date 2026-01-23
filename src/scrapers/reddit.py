"""Reddit scraper - supports both PRAW (with API key) and public JSON (no auth)."""

import asyncio
from typing import List, Optional
from datetime import datetime

import httpx
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


# Rate limiting for public JSON API
JSON_API_DELAY = 2.0  # Reddit wants 1 request per 2 seconds without auth


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
    """Scrape reviews and discussions from Reddit.
    
    Supports two modes:
    1. PRAW mode (with API credentials) - higher rate limits
    2. JSON mode (no auth required) - uses public .json endpoints
    """
    
    source_name = "reddit"
    
    def __init__(self):
        self.config = get_config()
        self._reddit = None
        self._use_json_api = False
        self._http_client = None
        logger.debug("Initialized RedditScraper")
    
    @property
    def http_client(self) -> httpx.AsyncClient:
        """Lazy-load async HTTP client for JSON API."""
        if self._http_client is None:
            self._http_client = httpx.AsyncClient(
                headers={
                    "User-Agent": self.config.reddit_user_agent or "ReviewMiner/1.0 (Educational Project)",
                },
                timeout=30.0,
                follow_redirects=True,
            )
        return self._http_client
    
    @property
    def reddit(self):
        """Lazy-load Reddit client. Falls back to JSON API if no credentials."""
        if self._reddit is None:
            client_id = self.config.reddit_client_id
            client_secret = self.config.reddit_client_secret
            
            # If no credentials, use JSON API instead
            if not client_id or not client_secret:
                logger.info("No Reddit API credentials found - using public JSON API (no auth required)")
                self._use_json_api = True
                return None
            
            try:
                import praw
                import prawcore
            except ImportError:
                logger.warning("PRAW not installed - falling back to JSON API")
                self._use_json_api = True
                return None
            
            user_agent = self.config.reddit_user_agent
            
            logger.debug("Initializing Reddit client with PRAW")
            self._reddit = praw.Reddit(
                client_id=client_id,
                client_secret=client_secret,
                user_agent=user_agent,
            )
        return self._reddit
    
    async def _json_search(
        self,
        query: str,
        subreddit: str = "all",
        limit: int = 25,
    ) -> List[dict]:
        """Search Reddit using public JSON API (no auth required)."""
        url = f"https://www.reddit.com/r/{subreddit}/search.json"
        params = {
            "q": query,
            "limit": min(limit, 100),  # Reddit caps at 100
            "sort": "relevance",
            "restrict_sr": "on" if subreddit != "all" else "off",
            "type": "link",
        }
        
        try:
            await asyncio.sleep(JSON_API_DELAY)  # Rate limit
            response = await self.http_client.get(url, params=params)
            response.raise_for_status()
            data = response.json()
            
            posts = []
            for child in data.get("data", {}).get("children", []):
                posts.append(child.get("data", {}))
            
            logger.debug("JSON API search returned %d posts", len(posts))
            return posts
            
        except httpx.HTTPStatusError as e:
            if e.response.status_code == 429:
                logger.warning("Rate limited by Reddit - waiting 60s")
                await asyncio.sleep(60)
                return await self._json_search(query, subreddit, limit)
            logger.error("Reddit JSON API error: %s", e)
            return []
        except Exception as e:
            logger.error("Reddit JSON API request failed: %s", e)
            return []
    
    async def _json_get_comments(self, post_id: str) -> List[dict]:
        """Get comments for a post using JSON API."""
        url = f"https://www.reddit.com/comments/{post_id}.json"
        
        try:
            await asyncio.sleep(JSON_API_DELAY)  # Rate limit
            response = await self.http_client.get(url)
            response.raise_for_status()
            data = response.json()
            
            comments = []
            if len(data) > 1:
                self._extract_comments_recursive(data[1].get("data", {}).get("children", []), comments)
            
            logger.debug("JSON API returned %d comments for post %s", len(comments), post_id)
            return comments
            
        except Exception as e:
            logger.error("Failed to get comments for %s: %s", post_id, e)
            return []
    
    def _extract_comments_recursive(self, children: list, comments: list, max_depth: int = 3, depth: int = 0):
        """Recursively extract comments from Reddit JSON structure."""
        if depth >= max_depth:
            return
            
        for child in children:
            if child.get("kind") != "t1":  # t1 = comment
                continue
            
            data = child.get("data", {})
            body = data.get("body", "")
            
            if body and body not in ("[deleted]", "[removed]") and len(body) >= 50:
                comments.append(data)
            
            # Recurse into replies
            replies = data.get("replies")
            if isinstance(replies, dict):
                reply_children = replies.get("data", {}).get("children", [])
                self._extract_comments_recursive(reply_children, comments, max_depth, depth + 1)
    
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
        
        # Check if we should use JSON API (no auth) or PRAW
        _ = self.reddit  # Trigger lazy init to set _use_json_api flag
        
        if self._use_json_api:
            return await self._search_and_scrape_json(query, subreddits, max_posts, pain_keywords)
        else:
            return await self._search_and_scrape_praw(query, subreddits, max_posts, pain_keywords)
    
    async def _search_and_scrape_json(
        self,
        query: str,
        subreddits: List[str],
        max_posts: int,
        pain_keywords: List[str],
    ) -> List[Review]:
        """Search and scrape using public JSON API (no auth required)."""
        logger.info("Using JSON API mode (no authentication)")
        
        all_reviews = []
        seen_ids = set()
        
        # Build search queries
        search_queries = [query]
        for keyword in pain_keywords[:2]:  # Limit queries due to rate limiting
            search_queries.append(f"{query} {keyword}")
        
        subreddit_str = "+".join(subreddits) if subreddits else "all"
        
        for search_query in search_queries:
            logger.debug("JSON search: %s in r/%s", search_query, subreddit_str)
            
            posts = await self._json_search(
                query=search_query,
                subreddit=subreddit_str,
                limit=max_posts // len(search_queries),
            )
            
            for post in posts:
                post_id = post.get("id")
                if not post_id or post_id in seen_ids:
                    continue
                seen_ids.add(post_id)
                
                # Extract from post body
                selftext = post.get("selftext", "")
                if selftext and selftext not in ("[deleted]", "[removed]") and len(selftext) >= 50:
                    all_reviews.append(Review(
                        source=self.source_name,
                        source_url=f"https://reddit.com{post.get('permalink', '')}",
                        product_title=post.get("title", ""),
                        author=post.get("author"),
                        rating=None,
                        review_text=selftext,
                        review_date=self._parse_utc_timestamp(post.get("created_utc")),
                    ))
                
                # Get comments
                comments = await self._json_get_comments(post_id)
                for comment in comments[:30]:  # Limit comments per post
                    author = comment.get("author", "")
                    if author.lower() in ("automoderator", "[deleted]"):
                        continue
                    
                    all_reviews.append(Review(
                        source=self.source_name,
                        source_url=f"https://reddit.com{comment.get('permalink', '')}",
                        product_title=post.get("title", ""),
                        author=author,
                        rating=None,
                        review_text=comment.get("body", ""),
                        review_date=self._parse_utc_timestamp(comment.get("created_utc")),
                    ))
        
        logger.info("JSON API collected %d reviews", len(all_reviews))
        return all_reviews
    
    def _parse_utc_timestamp(self, timestamp) -> Optional[datetime]:
        """Convert Reddit UTC timestamp to datetime."""
        if timestamp:
            try:
                return datetime.fromtimestamp(float(timestamp))
            except (ValueError, TypeError):
                pass
        return None
    
    async def _search_and_scrape_praw(
        self,
        query: str,
        subreddits: List[str],
        max_posts: int,
        pain_keywords: List[str],
    ) -> List[Review]:
        """Search and scrape using PRAW (requires API credentials)."""
        logger.info("Using PRAW mode (authenticated)")
        
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
    
    async def close(self):
        """Clean up resources."""
        if self._http_client:
            await self._http_client.aclose()
            self._http_client = None
    
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
