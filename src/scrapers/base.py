"""Base scraper abstract class."""

from abc import ABC, abstractmethod
from typing import List, Optional

from src.models import Review


class BaseScraper(ABC):
    """All scrapers must implement this interface."""
    
    source_name: str  # e.g., "amazon", "goodreads"
    
    @abstractmethod
    async def search(self, query: str, max_results: int = 50) -> List[str]:
        """Search for product/book URLs matching query."""
        pass
    
    @abstractmethod
    async def scrape_reviews(
        self,
        url: str,
        max_reviews: int = 100,
        min_rating: int = 1,
        max_rating: int = 3,
    ) -> List[Review]:
        """Scrape reviews from a specific product page."""
        pass
    
    async def scrape_from_search(
        self,
        query: str,
        max_products: int = 10,
        max_reviews_per_product: int = 50,
    ) -> List[Review]:
        """Convenience method: search then scrape."""
        urls = await self.search(query, max_products)
        all_reviews = []
        for url in urls:
            reviews = await self.scrape_reviews(url, max_reviews_per_product)
            all_reviews.extend(reviews)
        return all_reviews
