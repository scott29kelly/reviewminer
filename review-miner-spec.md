# Review Mining App - Complete Build Specification

## Overview

Build a Python CLI application that scrapes book/product reviews from multiple sources, analyzes them using Claude Sonnet 4.5, and extracts verbatim customer pain points for market research.

---

## Tech Stack

| Component | Technology | Why |
|-----------|------------|-----|
| **Language** | Python 3.11+ | Best scraping ecosystem |
| **LLM** | Claude Sonnet 4.5 (`claude-sonnet-4-5-20250929`) | Superior nuance for emotional/contextual extraction |
| **Scraping** | Playwright | Handles JS-rendered pages, stealth capabilities |
| **Database** | SQLite | Zero config, portable |
| **CLI Framework** | Typer | Clean interface, auto-generated help |
| **Terminal UI** | Rich | Progress bars, tables, styled output |
| **HTTP Client** | httpx | Async support, modern API |
| **HTML Parsing** | BeautifulSoup4 + lxml | Fast, reliable |

---

## Project Structure

```
review-miner/
├── main.py                     # CLI entry point
├── config.yaml                 # User-configurable settings
├── .env                        # API keys (gitignored)
├── .gitignore
├── requirements.txt
├── README.md
│
├── src/
│   ├── __init__.py
│   │
│   ├── scrapers/
│   │   ├── __init__.py
│   │   ├── base.py             # Abstract base scraper class
│   │   ├── amazon.py           # Amazon book reviews
│   │   ├── goodreads.py        # Goodreads reviews
│   │   ├── reddit.py           # Reddit discussions (PRAW)
│   │   ├── librarything.py     # LibraryThing reviews
│   │   └── csv_import.py       # Manual CSV fallback
│   │
│   ├── analyzer.py             # Claude API integration
│   ├── prompts.py              # System prompts (separated for easy tuning)
│   ├── database.py             # SQLite operations
│   ├── models.py               # Pydantic data models
│   └── exporter.py             # CSV, Markdown, JSON output
│
├── data/
│   ├── raw/                    # Raw scraped data dumps
│   ├── processed/              # Cleaned/deduplicated reviews
│   └── output/                 # Final pain point reports
│
└── tests/
    ├── __init__.py
    ├── test_scrapers.py
    ├── test_analyzer.py
    └── sample_reviews.json     # Test fixtures
```

---

## Database Schema

```sql
-- Reviews from all sources
CREATE TABLE reviews (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    source TEXT NOT NULL,           -- 'amazon', 'goodreads', 'reddit', etc.
    source_url TEXT,
    product_title TEXT,             -- Book title or thread title
    product_url TEXT,
    author TEXT,                    -- Reviewer username (if available)
    rating INTEGER,                 -- 1-5 stars (NULL for Reddit)
    review_text TEXT NOT NULL,
    review_date TEXT,
    scraped_at TEXT DEFAULT CURRENT_TIMESTAMP,
    processed BOOLEAN DEFAULT FALSE,
    UNIQUE(source, source_url, review_text)  -- Prevent duplicates
);

-- Extracted pain points
CREATE TABLE pain_points (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    review_id INTEGER NOT NULL,
    category TEXT NOT NULL,         -- e.g., "Too theoretical", "Outdated advice"
    verbatim_quote TEXT NOT NULL,
    emotional_intensity TEXT,       -- low, medium, high
    implied_need TEXT,              -- What they actually wanted
    extracted_at TEXT DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (review_id) REFERENCES reviews(id)
);

-- Track scraping jobs
CREATE TABLE scrape_jobs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    source TEXT NOT NULL,
    query TEXT,                     -- Search term or URL
    status TEXT DEFAULT 'pending',  -- pending, running, completed, failed
    reviews_found INTEGER DEFAULT 0,
    started_at TEXT,
    completed_at TEXT,
    error_message TEXT
);

-- Index for faster queries
CREATE INDEX idx_reviews_source ON reviews(source);
CREATE INDEX idx_reviews_processed ON reviews(processed);
CREATE INDEX idx_pain_points_category ON pain_points(category);
```

---

## Scraper Specifications

### Base Scraper Interface

```python
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
        max_rating: int = 3
    ) -> List[Review]:
        """Scrape reviews from a specific product page."""
        pass
    
    async def scrape_from_search(
        self, 
        query: str, 
        max_products: int = 10,
        max_reviews_per_product: int = 50
    ) -> List[Review]:
        """Convenience method: search then scrape."""
        urls = await self.search(query, max_products)
        all_reviews = []
        for url in urls:
            reviews = await self.scrape_reviews(url, max_reviews_per_product)
            all_reviews.extend(reviews)
        return all_reviews
```

### Amazon Scraper

**Target:** `amazon.com/product-reviews/` pages

**Strategy:**
1. Use Playwright with stealth settings (random delays, realistic viewport)
2. Navigate to book's review page filtered by star rating
3. Extract review cards from `.review` elements
4. Handle pagination via "Next page" button
5. Implement exponential backoff on rate limits

**Key selectors (may need updating):**
```python
SELECTORS = {
    "review_cards": "[data-hook='review']",
    "review_text": "[data-hook='review-body'] span",
    "review_rating": "[data-hook='review-star-rating'] span",
    "review_date": "[data-hook='review-date']",
    "review_author": ".a-profile-name",
    "next_page": ".a-pagination .a-last a",
    "filter_stars": "a[href*='filterByStar']"
}
```

**Rate limiting:** 
- 3-7 second random delay between pages
- 30-60 second delay between products
- Rotate user agents

### Goodreads Scraper

**Target:** `goodreads.com/book/show/` review pages

**Strategy:**
1. Use httpx + BeautifulSoup (pages are mostly static HTML)
2. Navigate to book's reviews tab
3. Filter by rating (1-3 stars) via URL params
4. Extract from review containers
5. Handle "Show more" AJAX pagination

**Key selectors:**
```python
SELECTORS = {
    "review_cards": ".review",
    "review_text": ".reviewText span",
    "review_rating": ".staticStars",
    "review_date": ".reviewDate",
    "review_author": ".user",
    "book_title": "#bookTitle"
}
```

**Rate limiting:**
- 2-4 second delay between requests
- Respect robots.txt

### Reddit Scraper

**Target:** Subreddits like r/books, r/suggestmeabook, r/selfimprovement, niche subreddits

**Strategy:**
1. Use PRAW (Python Reddit API Wrapper) - official API
2. Search for book titles + keywords like "disappointed", "waste", "didn't help"
3. Extract both posts and comments
4. No star ratings - all content is potentially useful

**Search queries to combine with book/topic:**
```python
PAIN_KEYWORDS = [
    "disappointed", "waste of time", "didn't help", 
    "overrated", "not worth", "struggled with",
    "couldn't finish", "expected more", "misleading"
]
```

**PRAW setup:**
```python
import praw

reddit = praw.Reddit(
    client_id="YOUR_CLIENT_ID",
    client_secret="YOUR_CLIENT_SECRET",
    user_agent="review-miner/1.0"
)

# Search example
subreddit = reddit.subreddit("books+suggestmeabook")
for submission in subreddit.search(f'"{book_title}" disappointed', limit=50):
    # Process submission.selftext and submission.comments
```

### LibraryThing Scraper

**Target:** `librarything.com/work/` review pages

**Strategy:**
1. httpx + BeautifulSoup
2. Reviews are on `/reviews` subpage
3. Can filter by rating
4. Smaller corpus but often more detailed reviews

### CSV Import (Fallback)

**Purpose:** Allow manual data entry or import from other tools

**Expected format:**
```csv
source,product_title,rating,review_text,review_date
manual,Deep Work,2,"I found the advice too vague and hard to implement...",2024-01-15
```

---

## Analyzer Specification

### Claude API Integration

```python
import anthropic
from typing import List
from src.models import Review, PainPoint
from src.prompts import PAIN_POINT_EXTRACTOR

class PainPointAnalyzer:
    def __init__(self, api_key: str):
        self.client = anthropic.Anthropic(api_key=api_key)
        self.model = "claude-sonnet-4-5-20250929"
    
    async def analyze_batch(
        self, 
        reviews: List[Review],
        batch_size: int = 20
    ) -> List[PainPoint]:
        """
        Analyze reviews in batches to manage token usage.
        Returns extracted pain points.
        """
        all_pain_points = []
        
        for i in range(0, len(reviews), batch_size):
            batch = reviews[i:i + batch_size]
            batch_text = self._format_reviews(batch)
            
            response = self.client.messages.create(
                model=self.model,
                max_tokens=4096,
                system=PAIN_POINT_EXTRACTOR,
                messages=[{
                    "role": "user",
                    "content": f"Analyze these reviews and extract pain points:\n\n{batch_text}"
                }]
            )
            
            pain_points = self._parse_response(response.content[0].text, batch)
            all_pain_points.extend(pain_points)
        
        return all_pain_points
    
    def _format_reviews(self, reviews: List[Review]) -> str:
        """Format reviews for the prompt."""
        formatted = []
        for i, review in enumerate(reviews, 1):
            formatted.append(
                f"[Review {i}] Source: {review.source} | "
                f"Rating: {review.rating or 'N/A'} stars\n"
                f"{review.review_text}\n"
            )
        return "\n---\n".join(formatted)
    
    def _parse_response(self, response_text: str, source_reviews: List[Review]) -> List[PainPoint]:
        """Parse JSON response from Claude into PainPoint objects."""
        # Extract JSON from response (handle markdown code blocks)
        # Validate and create PainPoint objects
        # Link back to source review IDs
        pass
```

---

## System Prompt (prompts.py)

```python
PAIN_POINT_EXTRACTOR = """You are a market research analyst specializing in extracting customer pain points from product reviews. Your expertise is identifying the emotional undercurrents and unmet needs hidden in customer feedback.

## Your Task
Analyze the provided reviews and extract specific customer struggles, frustrations, and unmet needs. Focus on negative reviews (1-3 stars) and critical comments.

## Extraction Rules

### What to Extract
1. **Verbatim quotes only** - Copy exact words, do not paraphrase
2. **Complete thoughts** - Include enough context to understand the pain (minimum one full sentence)
3. **Emotional indicators** - Prioritize quotes with words like: frustrated, disappointed, struggled, couldn't, failed, waste, useless, confusing, misleading, expected, wished, hoped
4. **Specific complaints** - "The exercises were too vague" beats "I didn't like it"

### What to Ignore
- Positive feedback and praise
- Shipping/delivery complaints (unless relevant to product itself)
- Price complaints alone (unless tied to value/quality)
- Vague one-word reviews
- Reviews that are clearly fake/spam

### Categorization Guidelines
Assign each pain point to ONE category. Common categories include:
- **Too theoretical** - Lacks practical application
- **Outdated content** - Information is no longer relevant
- **Poor organization** - Hard to follow, jumps around
- **Unmet expectations** - Promised something it didn't deliver
- **Wrong audience** - Too basic/advanced for reader
- **Repetitive** - Same ideas recycled
- **Lacks depth** - Surface-level treatment
- **Writing quality** - Boring, dry, hard to read
- **Missing topics** - Expected content not included
- **Misleading title/description** - Bait and switch

Create new categories if needed, but keep them concise (2-4 words).

## Output Format
Return ONLY valid JSON array with this exact structure (no markdown, no explanation):
[
  {
    "review_number": 1,
    "pain_point_category": "Too theoretical",
    "verbatim_quote": "I kept waiting for concrete examples but every chapter was just abstract concepts with no real-world application.",
    "emotional_intensity": "high",
    "implied_need": "Wants actionable, step-by-step guidance they can implement immediately"
  }
]

## Emotional Intensity Scale
- **low**: Mild disappointment, constructive criticism
- **medium**: Clear frustration, would not recommend
- **high**: Strong negative emotion, anger, feeling deceived/wasted time

## Quality Standards
- Extract 2-5 pain points per review (if present)
- If a review has no extractable pain points, skip it
- Never fabricate or embellish quotes
- Preserve original spelling/grammar in quotes"""


# Alternative prompt for summarizing patterns across all extracted pain points
PATTERN_SYNTHESIZER = """You are a market research analyst creating an executive summary of customer pain points.

## Input
You will receive a list of extracted pain points from multiple reviews.

## Task
Identify the top recurring themes and patterns. For each theme:
1. Name the pattern clearly
2. Count how many times it appeared
3. Provide 2-3 representative verbatim quotes
4. Suggest what product/content could address this need

## Output Format
Return a structured report in Markdown format with:
- Executive summary (3-4 sentences)
- Top 5-10 pain point themes ranked by frequency
- Opportunity analysis for each theme
- Raw data appendix (all quotes grouped by theme)"""
```

---

## CLI Commands

```bash
# Initialize database and config
review-miner init

# Scrape from specific sources
review-miner scrape amazon "time management books" --max-products 10 --max-reviews 50
review-miner scrape goodreads "https://goodreads.com/book/show/123456" --max-reviews 100
review-miner scrape reddit "Deep Work Cal Newport" --subreddits books,productivity
review-miner scrape all "productivity books" --max-products 5

# Import from CSV
review-miner import data/raw/manual_reviews.csv

# Analyze collected reviews
review-miner analyze --source amazon  # Analyze only Amazon reviews
review-miner analyze --unprocessed    # Analyze only new reviews
review-miner analyze --all            # Re-analyze everything

# Export results
review-miner export csv data/output/pain_points.csv
review-miner export markdown data/output/report.md
review-miner export json data/output/pain_points.json

# View stats
review-miner stats                    # Show counts by source
review-miner stats --pain-points      # Show pain point categories

# Database management
review-miner db reset                 # Clear all data
review-miner db backup                # Create backup
```

---

## Configuration (config.yaml)

```yaml
# API Configuration
anthropic:
  model: "claude-sonnet-4-5-20250929"
  max_tokens: 4096
  batch_size: 20  # Reviews per API call

# Scraping Settings
scraping:
  default_max_reviews: 100
  default_max_products: 10
  
  amazon:
    enabled: true
    delay_min: 3
    delay_max: 7
    delay_between_products: 45
    user_agents:
      - "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36..."
      - "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36..."
  
  goodreads:
    enabled: true
    delay_min: 2
    delay_max: 4
  
  reddit:
    enabled: true
    subreddits:
      - books
      - suggestmeabook
      - selfimprovement
      - productivity
      - getdisciplined
    pain_keywords:
      - disappointed
      - waste of time
      - overrated
      - didn't help
  
  librarything:
    enabled: true
    delay_min: 2
    delay_max: 5

# Review Filtering
filtering:
  min_review_length: 50  # Characters
  max_review_length: 10000
  star_ratings: [1, 2, 3]  # Only scrape these ratings
  exclude_keywords:  # Skip reviews containing these
    - "I received this product for free"
    - "sponsored"

# Output Settings
output:
  default_format: "markdown"
  include_raw_reviews: false
  group_by_category: true
```

---

## Dependencies (requirements.txt)

```
# Core
anthropic>=0.40.0
httpx>=0.27.0
playwright>=1.40.0
beautifulsoup4>=4.12.0
lxml>=5.0.0
praw>=7.7.0

# Database
sqlite-utils>=3.35

# CLI & Display
typer>=0.12.0
rich>=13.7.0

# Data & Config
pydantic>=2.5.0
python-dotenv>=1.0.0
pyyaml>=6.0.0
pandas>=2.2.0

# Utilities
tenacity>=8.2.0  # Retry logic
fake-useragent>=1.4.0
```

---

## Implementation Order

### Phase 1: Foundation (Day 1)
1. Create project structure
2. Set up config.yaml and .env handling
3. Implement database.py with schema
4. Create Pydantic models
5. Build CSV importer (guaranteed working input)
6. Test with sample data

### Phase 2: Analyzer (Day 1-2)
1. Implement Claude API integration
2. Add the system prompt
3. Build JSON response parser
4. Test with imported CSV reviews
5. Implement batch processing

### Phase 3: Exporters (Day 2)
1. CSV exporter
2. Markdown report generator
3. JSON exporter

### Phase 4: Scrapers (Day 2-3)
1. Reddit scraper (easiest - official API)
2. Goodreads scraper (static HTML)
3. Amazon scraper (most complex)
4. LibraryThing scraper

### Phase 5: CLI Polish (Day 3)
1. Wire up all Typer commands
2. Add Rich progress bars
3. Error handling and logging
4. Help documentation

---

## Sample Test Data

Create `tests/sample_reviews.json` for testing without scraping:

```json
[
  {
    "source": "test",
    "product_title": "Deep Work by Cal Newport",
    "rating": 2,
    "review_text": "I was really excited about this book based on the reviews, but I found it incredibly disappointing. The first half is just Newport bragging about his academic achievements. When he finally gets to the 'how-to' section, it's incredibly vague. 'Schedule deep work blocks' - okay, but HOW do I protect that time when my boss expects instant responses? He clearly has never worked in a normal office environment. The examples are all professors and writers who have complete control over their schedules. Useless for anyone in a corporate job.",
    "review_date": "2024-06-15"
  },
  {
    "source": "test", 
    "product_title": "Atomic Habits by James Clear",
    "rating": 2,
    "review_text": "This could have been a blog post. The core ideas (habit stacking, 1% improvements, environment design) are solid but they're buried under endless repetitive stories and padding. I kept waiting for deeper insights that never came. If you've read any other habit book or even just browsed productivity Reddit, you won't find anything new here. Also frustrating that he barely addresses how to break BAD habits - it's 90% about building new ones.",
    "review_date": "2024-08-22"
  },
  {
    "source": "test",
    "product_title": "The 4-Hour Work Week by Tim Ferriss", 
    "rating": 1,
    "review_text": "Outdated garbage. Half the 'hacks' don't work anymore (virtual assistants, arbitrage businesses, etc). The whole premise assumes you already have a successful business or can easily start one. What about people with actual jobs and responsibilities? The arrogance is off the charts. This is lifestyle porn for people who want to fantasize about escaping their lives, not a practical guide for anyone living in reality.",
    "review_date": "2024-03-10"
  }
]
```

---

## Environment Variables (.env)

```bash
# Required
ANTHROPIC_API_KEY=sk-ant-...

# Optional (for Reddit scraping)
REDDIT_CLIENT_ID=your_client_id
REDDIT_CLIENT_SECRET=your_client_secret
REDDIT_USER_AGENT=review-miner/1.0 by /u/yourusername

# Optional (for proxy rotation)
PROXY_URL=http://user:pass@proxy:port
```

---

## Quick Start Commands for Claude Code

```bash
# Start the session with this context:
claude

# Then paste:
"""
Build a Review Mining CLI application following this specification. 

Start with Phase 1 (Foundation):
1. Create the full project structure
2. Implement config loading from config.yaml and .env
3. Create the SQLite database module with the schema
4. Build Pydantic models for Review and PainPoint
5. Implement the CSV importer
6. Create a simple test to verify the foundation works

Use Typer for CLI, Rich for terminal output, and follow the file structure exactly as specified.
"""
```

After Phase 1 works, continue with:
```
"Now implement Phase 2 - the Claude API analyzer. Use the PAIN_POINT_EXTRACTOR prompt from the spec. Include proper JSON parsing and error handling. Test it with the sample reviews."
```

---

## Success Criteria

The app is "working" when you can:

1. ✅ `review-miner import sample.csv` → Reviews appear in database
2. ✅ `review-miner analyze` → Pain points extracted and stored
3. ✅ `review-miner export markdown report.md` → Readable report generated
4. ✅ `review-miner scrape reddit "Deep Work"` → Reddit reviews collected
5. ✅ `review-miner scrape goodreads <url>` → Goodreads reviews collected
6. ✅ `review-miner scrape amazon "productivity books"` → Amazon reviews collected (may be flaky)
