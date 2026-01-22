# Scrapers Package
# Note: Only import base and csv_import by default
# Scraper implementations are imported lazily to avoid requiring all dependencies
from .base import BaseScraper
from .csv_import import CSVImporter

__all__ = [
    "BaseScraper",
    "CSVImporter",
]


def get_amazon_scraper():
    """Lazy import for Amazon scraper."""
    from .amazon import AmazonScraper
    return AmazonScraper


def get_goodreads_scraper():
    """Lazy import for Goodreads scraper."""
    from .goodreads import GoodreadsScraper
    return GoodreadsScraper


def get_librarything_scraper():
    """Lazy import for LibraryThing scraper."""
    from .librarything import LibraryThingScraper
    return LibraryThingScraper


def get_reddit_scraper():
    """Lazy import for Reddit scraper."""
    from .reddit import RedditScraper
    return RedditScraper
