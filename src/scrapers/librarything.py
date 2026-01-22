"""LibraryThing scraper using httpx and BeautifulSoup."""

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


class LibraryThingScraper(BaseScraper):
    """Scrape book reviews from LibraryThing."""
    
    source_name = "librarything"
    
    BASE_URL = "https://www.librarything.com"
    
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
        scraping_config = self.config.config.scraping.librarything
        self.delay_min = scraping_config.delay_min
        self.delay_max = scraping_config.delay_max
        self.timeout = getattr(
            self.config.config.scraping, "request_timeout", 30.0
        )
        logger.debug("Initialized LibraryThingScraper")
    
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
        """Search for books on LibraryThing."""
        search_url = f"{self.BASE_URL}/search.php?search={query.replace(' ', '+')}&searchtype=newwork_titles"
        logger.info("Searching LibraryThing for: %s", query)
        
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
            
            # Find work links in search results
            work_urls = []
            work_links = soup.select("a[href*='/work/']")
            
            seen = set()
            for link in work_links:
                href = link.get("href")
                if href and "/work/" in href and href not in seen:
                    seen.add(href)
                    full_url = urljoin(self.BASE_URL, href)
                    work_urls.append(full_url)
                    if len(work_urls) >= max_results:
                        break
            
            logger.info("Found %d works", len(work_urls))
            return work_urls
    
    async def scrape_reviews(
        self,
        url: str,
        max_reviews: int = 100,
        min_rating: int = 1,
        max_rating: int = 3,
    ) -> List[Review]:
        """Scrape reviews from a LibraryThing work page."""
        reviews = []
        logger.info("Scraping reviews from: %s", url)
        
        # Ensure we're on the reviews page
        if "/reviews" not in url:
            if url.endswith("/"):
                url = url + "reviews"
            else:
                url = url + "/reviews"
        
        async with httpx.AsyncClient(
            headers=self.HEADERS,
            follow_redirects=True,
            timeout=self.timeout,
        ) as client:
            # Get the work page first to extract title
            work_url = url.replace("/reviews", "")
            try:
                await asyncio.sleep(await self._get_delay())
                html = await self._fetch_page(client, work_url)
            except (ScraperError, httpx.HTTPError) as e:
                logger.error("Failed to fetch work page: %s", e)
                return []
            
            soup = BeautifulSoup(html, "lxml")
            book_title = self._extract_book_title(soup)
            logger.debug("Book title: %s", book_title)
            
            # Now get the reviews page
            try:
                await asyncio.sleep(await self._get_delay())
                html = await self._fetch_page(client, url)
            except (ScraperError, httpx.HTTPError) as e:
                logger.error("Failed to fetch reviews page: %s", e)
                return []
            
            soup = BeautifulSoup(html, "lxml")
            
            # Extract reviews
            review_elements = soup.select(".bookReview")
            if not review_elements:
                review_elements = soup.select(".review")
            
            logger.debug("Found %d review elements", len(review_elements))
            
            for element in review_elements:
                if len(reviews) >= max_reviews:
                    break
                
                review_text = self._extract_review_text(element)
                if not review_text or len(review_text) < 50:
                    continue
                
                rating = self._extract_rating(element)
                
                # Filter by rating if specified
                if rating and (rating < min_rating or rating > max_rating):
                    continue
                
                author = self._extract_author(element)
                review_date = self._extract_date(element)
                
                reviews.append(Review(
                    source=self.source_name,
                    source_url=url,
                    product_title=book_title,
                    product_url=work_url,
                    author=author,
                    rating=rating,
                    review_text=review_text,
                    review_date=review_date,
                ))
        
        logger.info("Scraped %d reviews total", len(reviews))
        return reviews
    
    def _extract_book_title(self, soup: BeautifulSoup) -> str:
        """Extract book title from page."""
        title_elem = soup.select_one("h1.headsummary")
        if title_elem:
            return title_elem.get_text(strip=True)
        
        title_elem = soup.select_one(".headsummary")
        if title_elem:
            return title_elem.get_text(strip=True)
        
        title_elem = soup.select_one("h1")
        if title_elem:
            return title_elem.get_text(strip=True)
        
        return "Unknown Book"
    
    def _extract_review_text(self, element) -> str:
        """Extract review text from a review element."""
        text_elem = element.select_one(".reviewText")
        if text_elem:
            return text_elem.get_text(strip=True)
        
        text_elem = element.select_one(".bookReviewBody")
        if text_elem:
            return text_elem.get_text(strip=True)
        
        # Try to get any paragraph content
        text_elem = element.select_one("p")
        if text_elem:
            return text_elem.get_text(strip=True)
        
        return ""
    
    def _extract_author(self, element) -> Optional[str]:
        """Extract reviewer name from a review element."""
        author_elem = element.select_one(".reviewer")
        if author_elem:
            return author_elem.get_text(strip=True)
        
        author_elem = element.select_one("a[href*='/profile/']")
        if author_elem:
            return author_elem.get_text(strip=True)
        
        return None
    
    def _extract_rating(self, element) -> Optional[int]:
        """Extract star rating from a review element."""
        # Try to find rating from stars
        stars_elem = element.select_one(".stars")
        if stars_elem:
            title = stars_elem.get("title", "")
            match = re.search(r"(\d+(?:\.\d+)?)", title)
            if match:
                return round(float(match.group(1)))
        
        # Try rating text
        rating_elem = element.select_one(".rating")
        if rating_elem:
            text = rating_elem.get_text()
            match = re.search(r"(\d+)", text)
            if match:
                return int(match.group(1))
        
        # Count star images
        star_imgs = element.select("img[src*='star']")
        if star_imgs:
            # Count filled vs empty stars
            filled = len([img for img in star_imgs if "full" in img.get("src", "").lower()])
            if filled > 0:
                return filled
        
        return None
    
    def _extract_date(self, element) -> Optional[str]:
        """Extract review date from a review element."""
        date_elem = element.select_one(".reviewDate")
        if date_elem:
            return date_elem.get_text(strip=True)
        
        date_elem = element.select_one(".date")
        if date_elem:
            return date_elem.get_text(strip=True)
        
        return None
