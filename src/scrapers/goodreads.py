"""Goodreads scraper using httpx and BeautifulSoup."""

import asyncio
import random
import re
from typing import List, Optional
from urllib.parse import urljoin

import httpx
from bs4 import BeautifulSoup
from tenacity import (
    retry,
    retry_if_exception_type,
    stop_after_attempt,
    wait_exponential,
)

from src.config import get_config
from src.exceptions import RateLimitError, ScraperError, ScraperTimeoutError
from src.logging_config import get_logger
from src.models import Review
from src.scrapers.base import BaseScraper


logger = get_logger(__name__)


class GoodreadsScraper(BaseScraper):
    """Scrape book reviews from Goodreads."""
    
    source_name = "goodreads"
    
    BASE_URL = "https://www.goodreads.com"
    
    HEADERS = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
        "Accept-Language": "en-US,en;q=0.5",
        "Accept-Encoding": "gzip, deflate, br",
        "Connection": "keep-alive",
    }
    
    # Retryable HTTP exceptions
    RETRYABLE_EXCEPTIONS = (
        httpx.TimeoutException,
        httpx.ConnectError,
        httpx.ReadError,
    )
    
    def __init__(self):
        self.config = get_config()
        scraping_config = self.config.config.scraping.goodreads
        self.delay_min = scraping_config.delay_min
        self.delay_max = scraping_config.delay_max
        self.timeout = getattr(
            self.config.config.scraping, "request_timeout", 30.0
        )
        logger.debug("Initialized GoodreadsScraper")
    
    async def _get_delay(self) -> float:
        """Get random delay between requests."""
        return random.uniform(self.delay_min, self.delay_max)
    
    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10),
        retry=retry_if_exception_type((
            httpx.TimeoutException,
            httpx.ConnectError,
            httpx.ReadError,
        )),
        reraise=True,
    )
    async def _fetch_page(self, client: httpx.AsyncClient, url: str) -> str:
        """Fetch a page with retry logic."""
        logger.debug("Fetching: %s", url)
        try:
            response = await client.get(url)
            
            # Check for rate limiting
            if response.status_code == 429:
                retry_after = int(response.headers.get("Retry-After", 60))
                logger.warning("Rate limited, retry after %d seconds", retry_after)
                raise RateLimitError("Rate limit exceeded", retry_after=retry_after)
            
            response.raise_for_status()
            return response.text
            
        except httpx.TimeoutException as e:
            logger.warning("Request timeout: %s", url)
            raise ScraperTimeoutError(f"Timeout fetching {url}") from e
    
    async def search(self, query: str, max_results: int = 50) -> List[str]:
        """Search for books on Goodreads."""
        search_url = f"{self.BASE_URL}/search?q={query.replace(' ', '+')}&search_type=books"
        logger.info("Searching Goodreads for: %s", query)
        
        async with httpx.AsyncClient(
            headers=self.HEADERS,
            follow_redirects=True,
            timeout=self.timeout,
        ) as client:
            try:
                html = await self._fetch_page(client, search_url)
            except (ScraperError, httpx.HTTPError) as e:
                logger.error("Search failed: %s", e)
                return []
            
            soup = BeautifulSoup(html, "lxml")
            
            # Find book links in search results
            book_urls = []
            book_links = soup.select("a.bookTitle")
            
            for link in book_links[:max_results]:
                href = link.get("href")
                if href:
                    full_url = urljoin(self.BASE_URL, href)
                    book_urls.append(full_url)
            
            logger.info("Found %d books", len(book_urls))
            return book_urls
    
    async def scrape_reviews(
        self,
        url: str,
        max_reviews: int = 100,
        min_rating: int = 1,
        max_rating: int = 3,
    ) -> List[Review]:
        """Scrape reviews from a Goodreads book page."""
        reviews = []
        logger.info("Scraping reviews from: %s", url)
        
        # Extract book ID from URL
        book_id = self._extract_book_id(url)
        if not book_id:
            logger.error("Could not extract book ID from URL: %s", url)
            return []
        
        async with httpx.AsyncClient(
            headers=self.HEADERS,
            follow_redirects=True,
            timeout=self.timeout,
        ) as client:
            # First, get book page to extract title
            try:
                html = await self._fetch_page(client, url)
            except (ScraperError, httpx.HTTPError) as e:
                logger.error("Failed to fetch book page: %s", e)
                return []
            
            soup = BeautifulSoup(html, "lxml")
            book_title = self._extract_book_title(soup)
            logger.debug("Book title: %s", book_title)
            
            # Try to scrape reviews from the reviews page
            # Filter by low ratings
            for rating in range(min_rating, max_rating + 1):
                if len(reviews) >= max_reviews:
                    break
                
                reviews_url = f"{self.BASE_URL}/book/reviews/{book_id}?rating={rating}"
                
                try:
                    await asyncio.sleep(await self._get_delay())
                    html = await self._fetch_page(client, reviews_url)
                except (ScraperError, httpx.HTTPError) as e:
                    logger.warning("Failed to fetch reviews for rating %d: %s", rating, e)
                    continue
                
                soup = BeautifulSoup(html, "lxml")
                page_reviews = self._extract_reviews(soup, book_title, url, rating)
                reviews.extend(page_reviews)
                logger.debug("Extracted %d reviews for rating %d", len(page_reviews), rating)
            
            # Also try to get reviews from the main book page
            # These are often embedded in the page
            page_reviews = self._extract_reviews_from_book_page(soup, book_title, url)
            for review in page_reviews:
                if review not in reviews and len(reviews) < max_reviews:
                    reviews.append(review)
        
        logger.info("Scraped %d reviews total", len(reviews[:max_reviews]))
        return reviews[:max_reviews]
    
    def _extract_book_id(self, url: str) -> Optional[str]:
        """Extract book ID from Goodreads URL."""
        # URL format: /book/show/12345-book-title
        match = re.search(r"/book/show/(\d+)", url)
        if match:
            return match.group(1)
        return None
    
    def _extract_book_title(self, soup: BeautifulSoup) -> str:
        """Extract book title from page."""
        # Try different selectors
        title_elem = soup.select_one("h1.Text__title1")
        if title_elem:
            return title_elem.get_text(strip=True)
        
        title_elem = soup.select_one("[data-testid='bookTitle']")
        if title_elem:
            return title_elem.get_text(strip=True)
        
        title_elem = soup.select_one("#bookTitle")
        if title_elem:
            return title_elem.get_text(strip=True)
        
        return "Unknown Book"
    
    def _extract_reviews(
        self,
        soup: BeautifulSoup,
        book_title: str,
        book_url: str,
        rating: Optional[int] = None,
    ) -> List[Review]:
        """Extract reviews from a reviews page."""
        reviews = []
        
        # Try modern Goodreads layout
        review_cards = soup.select("[data-testid='review']")
        if not review_cards:
            # Try older layout
            review_cards = soup.select(".review")
        
        for card in review_cards:
            review_text = self._extract_review_text(card)
            if not review_text or len(review_text) < 50:
                continue
            
            author = self._extract_author(card)
            review_date = self._extract_date(card)
            extracted_rating = rating or self._extract_rating(card)
            
            reviews.append(Review(
                source=self.source_name,
                source_url=book_url,
                product_title=book_title,
                product_url=book_url,
                author=author,
                rating=extracted_rating,
                review_text=review_text,
                review_date=review_date,
            ))
        
        return reviews
    
    def _extract_reviews_from_book_page(
        self,
        soup: BeautifulSoup,
        book_title: str,
        book_url: str,
    ) -> List[Review]:
        """Extract reviews embedded in the main book page."""
        reviews = []
        
        # Modern layout review containers
        review_sections = soup.select("[data-testid='reviewCard']")
        if not review_sections:
            review_sections = soup.select(".ReviewCard")
        
        for section in review_sections:
            review_text = self._extract_review_text(section)
            if not review_text or len(review_text) < 50:
                continue
            
            rating = self._extract_rating(section)
            
            # Only include low-rated reviews (1-3 stars)
            if rating and rating > 3:
                continue
            
            author = self._extract_author(section)
            review_date = self._extract_date(section)
            
            reviews.append(Review(
                source=self.source_name,
                source_url=book_url,
                product_title=book_title,
                product_url=book_url,
                author=author,
                rating=rating,
                review_text=review_text,
                review_date=review_date,
            ))
        
        return reviews
    
    def _extract_review_text(self, element) -> str:
        """Extract review text from a review element."""
        # Try different selectors
        text_elem = element.select_one("[data-testid='contentContainer']")
        if text_elem:
            return text_elem.get_text(strip=True)
        
        text_elem = element.select_one(".ReviewText__content")
        if text_elem:
            return text_elem.get_text(strip=True)
        
        text_elem = element.select_one(".reviewText span")
        if text_elem:
            return text_elem.get_text(strip=True)
        
        text_elem = element.select_one(".reviewText")
        if text_elem:
            return text_elem.get_text(strip=True)
        
        return ""
    
    def _extract_author(self, element) -> Optional[str]:
        """Extract reviewer name from a review element."""
        author_elem = element.select_one("[data-testid='name']")
        if author_elem:
            return author_elem.get_text(strip=True)
        
        author_elem = element.select_one(".user")
        if author_elem:
            return author_elem.get_text(strip=True)
        
        return None
    
    def _extract_rating(self, element) -> Optional[int]:
        """Extract star rating from a review element."""
        # Try to find rating from stars
        stars_elem = element.select_one("[data-testid='rating']")
        if stars_elem:
            rating_text = stars_elem.get("aria-label", "")
            match = re.search(r"(\d)", rating_text)
            if match:
                return int(match.group(1))
        
        # Try older format
        stars_elem = element.select_one(".staticStars")
        if stars_elem:
            stars_class = stars_elem.get("class", [])
            for cls in stars_class:
                match = re.search(r"stars(\d)", cls)
                if match:
                    return int(match.group(1))
        
        # Count filled stars
        filled_stars = element.select(".RatingStar__filledStar")
        if filled_stars:
            return len(filled_stars)
        
        return None
    
    def _extract_date(self, element) -> Optional[str]:
        """Extract review date from a review element."""
        date_elem = element.select_one("[data-testid='reviewDate']")
        if date_elem:
            return date_elem.get_text(strip=True)
        
        date_elem = element.select_one(".reviewDate")
        if date_elem:
            return date_elem.get_text(strip=True)
        
        return None
    
    def scrape_book_reviews(
        self,
        query: str,
        max_reviews: int = 100,
        max_books: int = 10,
    ) -> List[Review]:
        """Search for books by topic and scrape reviews from multiple books.
        
        This is a synchronous wrapper for topic-based scraping.
        """
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            return loop.run_until_complete(
                self._scrape_book_reviews_async(query, max_reviews, max_books)
            )
        finally:
            loop.close()
    
    async def _scrape_book_reviews_async(
        self,
        query: str,
        max_reviews: int = 100,
        max_books: int = 10,
    ) -> List[Review]:
        """Search for books by topic and scrape reviews from multiple books."""
        logger.info("Starting topic-based scrape for: %s", query)
        
        # Search for books matching the topic
        book_urls = await self.search(query, max_books)
        
        if not book_urls:
            logger.warning("No books found for query: %s", query)
            return []
        
        all_reviews = []
        reviews_per_book = max(1, max_reviews // len(book_urls))
        
        for i, url in enumerate(book_urls, 1):
            if len(all_reviews) >= max_reviews:
                break
            
            logger.info("Scraping book %d/%d: %s", i, len(book_urls), url[:80])
            
            try:
                reviews = await self.scrape_reviews(
                    url,
                    max_reviews=reviews_per_book,
                )
                all_reviews.extend(reviews)
                logger.info("Got %d reviews from book %d", len(reviews), i)
                
                # Delay between books
                if i < len(book_urls):
                    await asyncio.sleep(await self._get_delay() * 2)
                    
            except Exception as e:
                logger.warning("Failed to scrape book %s: %s", url, e)
                continue
        
        logger.info("Total reviews scraped: %d", len(all_reviews[:max_reviews]))
        return all_reviews[:max_reviews]
