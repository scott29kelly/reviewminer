"""Amazon scraper using Playwright with stealth capabilities."""

import asyncio
import random
import re
from typing import List, Optional
from urllib.parse import urljoin

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


class AmazonScraper(BaseScraper):
    """Scrape book reviews from Amazon using Playwright."""
    
    source_name = "amazon"
    
    BASE_URL = "https://www.amazon.com"
    
    # Selectors for Amazon review pages
    SELECTORS = {
        "review_cards": "[data-hook='review']",
        "review_text": "[data-hook='review-body'] span",
        "review_rating": "[data-hook='review-star-rating'] span, [data-hook='cmps-review-star-rating'] span",
        "review_date": "[data-hook='review-date']",
        "review_author": ".a-profile-name",
        "next_page": ".a-pagination .a-last a",
        "filter_stars": "a[href*='filterByStar']",
        "product_title": "#productTitle, [data-hook='product-link']",
        "search_results": ".s-result-item[data-asin]",
        "search_link": "h2 a.a-link-normal",
        "captcha": "#captchacharacters",
    }
    
    def __init__(self):
        self.config = get_config()
        scraping_config = self.config.config.scraping.amazon
        self.delay_min = scraping_config.delay_min
        self.delay_max = scraping_config.delay_max
        self.delay_between_products = scraping_config.delay_between_products
        self.user_agents = scraping_config.user_agents or [
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        ]
        self._browser = None
        self._context = None
        logger.debug("Initialized AmazonScraper")
    
    async def _get_delay(self) -> float:
        """Get random delay between requests."""
        return random.uniform(self.delay_min, self.delay_max)
    
    async def _get_browser(self):
        """Get or create Playwright browser."""
        if self._browser is None:
            try:
                from playwright.async_api import async_playwright
            except ImportError:
                raise ImportError(
                    "Playwright is required for Amazon scraping. "
                    "Install with: pip install playwright && playwright install chromium"
                )
            
            logger.debug("Launching browser")
            self._playwright = await async_playwright().start()
            self._browser = await self._playwright.chromium.launch(
                headless=True,
                args=[
                    "--disable-blink-features=AutomationControlled",
                    "--disable-dev-shm-usage",
                    "--no-sandbox",
                ]
            )
        
        return self._browser
    
    async def _get_context(self):
        """Get or create browser context with stealth settings."""
        if self._context is None:
            browser = await self._get_browser()
            
            user_agent = random.choice(self.user_agents)
            logger.debug("Using user agent: %s", user_agent[:50])
            
            self._context = await browser.new_context(
                user_agent=user_agent,
                viewport={"width": 1920, "height": 1080},
                locale="en-US",
                timezone_id="America/New_York",
                extra_http_headers={
                    "Accept-Language": "en-US,en;q=0.9",
                },
            )
            
            # Add stealth scripts
            await self._context.add_init_script("""
                // Overwrite the `navigator.webdriver` property
                Object.defineProperty(navigator, 'webdriver', {
                    get: () => undefined,
                });
                
                // Overwrite the `navigator.plugins` property
                Object.defineProperty(navigator, 'plugins', {
                    get: () => [1, 2, 3, 4, 5],
                });
                
                // Overwrite the `navigator.languages` property
                Object.defineProperty(navigator, 'languages', {
                    get: () => ['en-US', 'en'],
                });
            """)
        
        return self._context
    
    async def _close(self):
        """Close browser and playwright."""
        if self._context:
            await self._context.close()
            self._context = None
        if self._browser:
            await self._browser.close()
            self._browser = None
        if hasattr(self, "_playwright") and self._playwright:
            await self._playwright.stop()
            self._playwright = None
        logger.debug("Browser closed")
    
    async def _check_for_captcha(self, page) -> bool:
        """Check if we've hit a CAPTCHA page."""
        captcha = await page.query_selector(self.SELECTORS["captcha"])
        if captcha:
            logger.warning("CAPTCHA detected")
            return True
        return False
    
    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=5, max=30),
        retry=retry_if_exception_type((TimeoutError,)),
        reraise=True,
    )
    async def _navigate_with_retry(self, page, url: str):
        """Navigate to a page with retry logic."""
        logger.debug("Navigating to: %s", url)
        try:
            await page.goto(url, wait_until="networkidle", timeout=30000)
            
            # Check for CAPTCHA
            if await self._check_for_captcha(page):
                raise RateLimitError("CAPTCHA detected - rate limited by Amazon")
            
        except TimeoutError as e:
            logger.warning("Page load timeout: %s", url)
            raise ScraperTimeoutError(f"Timeout loading {url}") from e
    
    async def search(self, query: str, max_results: int = 50) -> List[str]:
        """Search for books on Amazon."""
        search_url = f"{self.BASE_URL}/s?k={query.replace(' ', '+')}&i=stripbooks"
        logger.info("Searching Amazon for: %s", query)
        
        try:
            context = await self._get_context()
            page = await context.new_page()
            
            await self._navigate_with_retry(page, search_url)
            await asyncio.sleep(await self._get_delay())
            
            # Extract product URLs
            product_urls = []
            items = await page.query_selector_all(self.SELECTORS["search_results"])
            
            for item in items[:max_results]:
                link = await item.query_selector(self.SELECTORS["search_link"])
                if link:
                    href = await link.get_attribute("href")
                    if href:
                        full_url = urljoin(self.BASE_URL, href)
                        # Clean URL
                        if "/dp/" in full_url:
                            product_urls.append(full_url.split("?")[0])
            
            await page.close()
            logger.info("Found %d products", len(product_urls))
            return product_urls
            
        except ScraperError:
            raise
        except Exception as e:
            logger.error("Search failed: %s", e)
            return []
    
    async def scrape_reviews(
        self,
        url: str,
        max_reviews: int = 100,
        min_rating: int = 1,
        max_rating: int = 3,
    ) -> List[Review]:
        """Scrape reviews from an Amazon product page."""
        reviews = []
        logger.info("Scraping reviews from: %s", url)
        
        # Convert product URL to reviews URL
        asin = self._extract_asin(url)
        if not asin:
            logger.error("Could not extract ASIN from URL: %s", url)
            return []
        
        try:
            context = await self._get_context()
            page = await context.new_page()
            
            # Get product title first
            product_url = f"{self.BASE_URL}/dp/{asin}"
            await self._navigate_with_retry(page, product_url)
            await asyncio.sleep(await self._get_delay())
            
            title_elem = await page.query_selector(self.SELECTORS["product_title"])
            product_title = await title_elem.inner_text() if title_elem else "Unknown Product"
            product_title = product_title.strip()
            logger.debug("Product title: %s", product_title)
            
            # Scrape reviews filtered by star rating
            for star_rating in range(min_rating, max_rating + 1):
                if len(reviews) >= max_reviews:
                    break
                
                reviews_url = f"{self.BASE_URL}/product-reviews/{asin}?filterByStar={self._star_filter(star_rating)}&reviewerType=all_reviews"
                logger.debug("Scraping %d-star reviews", star_rating)
                
                page_num = 1
                while len(reviews) < max_reviews:
                    paginated_url = f"{reviews_url}&pageNumber={page_num}"
                    
                    try:
                        await self._navigate_with_retry(page, paginated_url)
                        await asyncio.sleep(await self._get_delay())
                    except ScraperError as e:
                        logger.warning("Failed to load page %d: %s", page_num, e)
                        break
                    
                    # Extract reviews from page
                    review_cards = await page.query_selector_all(self.SELECTORS["review_cards"])
                    
                    if not review_cards:
                        logger.debug("No more reviews on page %d", page_num)
                        break
                    
                    for card in review_cards:
                        if len(reviews) >= max_reviews:
                            break
                        
                        review = await self._extract_review(card, product_title, product_url, star_rating)
                        if review:
                            reviews.append(review)
                    
                    logger.debug("Page %d: extracted %d reviews", page_num, len(review_cards))
                    
                    # Check for next page
                    next_btn = await page.query_selector(self.SELECTORS["next_page"])
                    if not next_btn:
                        break
                    
                    page_num += 1
                    await asyncio.sleep(await self._get_delay())
            
            await page.close()
            
        except ScraperError:
            raise
        except Exception as e:
            logger.error("Scraping failed: %s", e, exc_info=True)
        
        logger.info("Scraped %d reviews total", len(reviews))
        return reviews
    
    async def scrape_from_search(
        self,
        query: str,
        max_products: int = 10,
        max_reviews_per_product: int = 50,
    ) -> List[Review]:
        """Search then scrape reviews from products."""
        logger.info("Starting search and scrape for: %s", query)
        try:
            urls = await self.search(query, max_products)
            all_reviews = []
            
            for i, url in enumerate(urls, 1):
                logger.info("Scraping product %d/%d", i, len(urls))
                reviews = await self.scrape_reviews(url, max_reviews_per_product)
                all_reviews.extend(reviews)
                
                # Longer delay between products
                if i < len(urls):
                    logger.debug("Waiting %d seconds before next product", self.delay_between_products)
                    await asyncio.sleep(self.delay_between_products)
            
            logger.info("Total reviews scraped: %d", len(all_reviews))
            return all_reviews
        finally:
            await self._close()
    
    def _extract_asin(self, url: str) -> Optional[str]:
        """Extract ASIN from Amazon URL."""
        # Try /dp/ASIN format
        match = re.search(r"/dp/([A-Z0-9]{10})", url)
        if match:
            return match.group(1)
        
        # Try /product/ASIN format
        match = re.search(r"/product/([A-Z0-9]{10})", url)
        if match:
            return match.group(1)
        
        # Try /gp/product/ASIN format
        match = re.search(r"/gp/product/([A-Z0-9]{10})", url)
        if match:
            return match.group(1)
        
        return None
    
    def _star_filter(self, stars: int) -> str:
        """Convert star count to Amazon filter value."""
        mapping = {
            1: "one_star",
            2: "two_star",
            3: "three_star",
            4: "four_star",
            5: "five_star",
        }
        return mapping.get(stars, "three_star")
    
    async def _extract_review(
        self,
        card,
        product_title: str,
        product_url: str,
        expected_rating: int,
    ) -> Optional[Review]:
        """Extract review data from a review card element."""
        try:
            # Get review text
            text_elem = await card.query_selector(self.SELECTORS["review_text"])
            if not text_elem:
                return None
            
            review_text = await text_elem.inner_text()
            review_text = review_text.strip()
            
            if len(review_text) < 50:
                return None
            
            # Get author
            author = None
            author_elem = await card.query_selector(self.SELECTORS["review_author"])
            if author_elem:
                author = await author_elem.inner_text()
                author = author.strip()
            
            # Get date
            review_date = None
            date_elem = await card.query_selector(self.SELECTORS["review_date"])
            if date_elem:
                date_text = await date_elem.inner_text()
                # Extract date from "Reviewed in the United States on January 1, 2024"
                match = re.search(r"on (.+)$", date_text)
                if match:
                    review_date = match.group(1).strip()
            
            # Get rating (verify it matches expected)
            rating = expected_rating
            rating_elem = await card.query_selector(self.SELECTORS["review_rating"])
            if rating_elem:
                rating_text = await rating_elem.inner_text()
                match = re.search(r"(\d+\.?\d*)", rating_text)
                if match:
                    rating = int(float(match.group(1)))
            
            return Review(
                source=self.source_name,
                source_url=product_url,
                product_title=product_title,
                product_url=product_url,
                author=author,
                rating=rating,
                review_text=review_text,
                review_date=review_date,
            )
            
        except Exception as e:
            logger.debug("Failed to extract review: %s", e)
            return None
