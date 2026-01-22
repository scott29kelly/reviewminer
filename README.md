# Review Miner

A Python CLI application that scrapes book/product reviews from multiple sources, analyzes them using Claude Sonnet 4.5, and extracts verbatim customer pain points for market research.

## Features

- **Multi-source scraping**: Amazon, Goodreads, Reddit, LibraryThing
- **AI-powered analysis**: Extract pain points using Claude Sonnet 4.5
- **Flexible export**: CSV, Markdown, and JSON output formats
- **CLI interface**: Simple commands with Rich terminal UI

## Installation

```bash
# Clone the repository
git clone <repository-url>
cd review-miner

# Create virtual environment
python -m venv venv
venv\Scripts\activate  # Windows
# source venv/bin/activate  # Linux/Mac

# Install dependencies
pip install -r requirements.txt

# Install Playwright browsers (for Amazon scraping)
playwright install chromium
```

## Configuration

1. Copy `.env.example` to `.env` and fill in your API keys:

```bash
copy .env.example .env
```

2. Edit `config.yaml` to customize scraping behavior.

## Usage

```bash
# Initialize database
python main.py init

# Import reviews from CSV
python main.py import data/raw/reviews.csv

# Scrape reviews
python main.py scrape amazon "time management books" --max-products 10
python main.py scrape reddit "Deep Work Cal Newport" --subreddits books,productivity
python main.py scrape goodreads "https://goodreads.com/book/show/123456"

# Analyze collected reviews
python main.py analyze --unprocessed

# Export results
python main.py export markdown data/output/report.md
python main.py export csv data/output/pain_points.csv

# View statistics
python main.py stats
python main.py stats --pain-points
```

## Project Structure

```
review-miner/
├── main.py                 # CLI entry point
├── config.yaml             # User-configurable settings
├── .env                    # API keys (gitignored)
├── src/
│   ├── scrapers/           # Source-specific scrapers
│   ├── analyzer.py         # Claude API integration
│   ├── database.py         # SQLite operations
│   ├── models.py           # Pydantic data models
│   └── exporter.py         # Output formatters
└── data/
    ├── raw/                # Raw scraped data
    ├── processed/          # Cleaned reviews
    └── output/             # Final reports
```

## License

MIT
