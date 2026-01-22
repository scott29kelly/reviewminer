"""Configuration loading and management."""

import os
from pathlib import Path
from typing import Optional

import yaml
from dotenv import load_dotenv
from pydantic import BaseModel, Field


class AnthropicConfig(BaseModel):
    """Anthropic API configuration."""
    model: str = "claude-sonnet-4-5-20250929"
    max_tokens: int = 4096
    batch_size: int = 20
    max_retries: int = 3
    retry_min_wait: float = 2.0  # seconds
    retry_max_wait: float = 30.0  # seconds


class AmazonScraperConfig(BaseModel):
    """Amazon scraper configuration."""
    enabled: bool = True
    delay_min: float = 3
    delay_max: float = 7
    delay_between_products: float = 45
    user_agents: list[str] = Field(default_factory=list)


class GoodreadsScraperConfig(BaseModel):
    """Goodreads scraper configuration."""
    enabled: bool = True
    delay_min: float = 2
    delay_max: float = 4


class RedditScraperConfig(BaseModel):
    """Reddit scraper configuration."""
    enabled: bool = True
    subreddits: list[str] = Field(default_factory=lambda: ["books", "suggestmeabook"])
    pain_keywords: list[str] = Field(default_factory=lambda: ["disappointed", "waste of time"])


class LibraryThingScraperConfig(BaseModel):
    """LibraryThing scraper configuration."""
    enabled: bool = True
    delay_min: float = 2
    delay_max: float = 5


class ScrapingConfig(BaseModel):
    """Scraping configuration."""
    default_max_reviews: int = 100
    default_max_products: int = 10
    request_timeout: float = 30.0  # seconds
    max_retries: int = 3
    retry_min_wait: float = 2.0  # seconds
    retry_max_wait: float = 10.0  # seconds
    amazon: AmazonScraperConfig = Field(default_factory=AmazonScraperConfig)
    goodreads: GoodreadsScraperConfig = Field(default_factory=GoodreadsScraperConfig)
    reddit: RedditScraperConfig = Field(default_factory=RedditScraperConfig)
    librarything: LibraryThingScraperConfig = Field(default_factory=LibraryThingScraperConfig)


class FilteringConfig(BaseModel):
    """Review filtering configuration."""
    min_review_length: int = 50
    max_review_length: int = 10000
    star_ratings: list[int] = Field(default_factory=lambda: [1, 2, 3])
    exclude_keywords: list[str] = Field(default_factory=list)


class OutputConfig(BaseModel):
    """Output configuration."""
    default_format: str = "markdown"
    include_raw_reviews: bool = False
    group_by_category: bool = True


class DatabaseConfig(BaseModel):
    """Database configuration."""
    path: str = "data/review_miner.db"


class AppConfig(BaseModel):
    """Main application configuration."""
    anthropic: AnthropicConfig = Field(default_factory=AnthropicConfig)
    scraping: ScrapingConfig = Field(default_factory=ScrapingConfig)
    filtering: FilteringConfig = Field(default_factory=FilteringConfig)
    output: OutputConfig = Field(default_factory=OutputConfig)
    database: DatabaseConfig = Field(default_factory=DatabaseConfig)


class Config:
    """Configuration manager that loads from YAML and environment variables."""
    
    _instance: Optional["Config"] = None
    _config: Optional[AppConfig] = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self):
        if self._config is None:
            self.load()
    
    def load(self, config_path: str = "config.yaml") -> None:
        """Load configuration from YAML file and environment variables."""
        # Load environment variables from .env
        load_dotenv()
        
        # Load YAML config
        config_file = Path(config_path)
        if config_file.exists():
            with open(config_file, "r") as f:
                yaml_config = yaml.safe_load(f) or {}
        else:
            yaml_config = {}
        
        self._config = AppConfig(**yaml_config)
    
    @property
    def config(self) -> AppConfig:
        """Get the loaded configuration."""
        if self._config is None:
            self.load()
        return self._config
    
    @property
    def anthropic_api_key(self) -> str:
        """Get Anthropic API key from environment."""
        key = os.getenv("ANTHROPIC_API_KEY", "")
        if not key:
            raise ValueError("ANTHROPIC_API_KEY not set in environment")
        return key
    
    @property
    def reddit_client_id(self) -> Optional[str]:
        """Get Reddit client ID from environment."""
        return os.getenv("REDDIT_CLIENT_ID")
    
    @property
    def reddit_client_secret(self) -> Optional[str]:
        """Get Reddit client secret from environment."""
        return os.getenv("REDDIT_CLIENT_SECRET")
    
    @property
    def reddit_user_agent(self) -> str:
        """Get Reddit user agent from environment."""
        return os.getenv("REDDIT_USER_AGENT", "review-miner/1.0")
    
    @property
    def proxy_url(self) -> Optional[str]:
        """Get proxy URL from environment."""
        return os.getenv("PROXY_URL")


def get_config() -> Config:
    """Get the configuration singleton."""
    return Config()
