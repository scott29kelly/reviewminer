#!/usr/bin/env python3
"""Review Miner CLI - Extract customer pain points from product reviews."""

import sys
from pathlib import Path
from typing import Optional

import typer
from rich.console import Console
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.table import Table

from src.logging_config import setup_logging, get_logger

# Initialize app
app = typer.Typer(
    name="review-miner",
    help="Extract customer pain points from product reviews using AI.",
    no_args_is_help=True,
)

# Subcommand groups
scrape_app = typer.Typer(help="Scrape reviews from various sources.")
db_app = typer.Typer(help="Database management commands.")
app.add_typer(scrape_app, name="scrape")
app.add_typer(db_app, name="db")

console = Console()
logger = get_logger(__name__)


# ============== App Callback for Global Options ==============


@app.callback()
def main_callback(
    verbose: bool = typer.Option(False, "--verbose", "-v", help="Enable debug logging"),
    quiet: bool = typer.Option(False, "--quiet", "-q", help="Suppress info messages"),
):
    """Review Miner - Extract customer pain points from product reviews using AI."""
    setup_logging(verbose=verbose, quiet=quiet, console=console)


# ============== Init Command ==============


@app.command()
def init():
    """Initialize the database and configuration."""
    from src.config import get_config
    from src.database import get_database
    from src.exceptions import ConfigError, DatabaseError
    
    logger.info("Initializing Review Miner")
    
    try:
        with console.status("[bold green]Initializing Review Miner..."):
            # Load config to validate it
            config = get_config()
            logger.debug("Configuration loaded successfully")
            
            # Initialize database
            db = get_database()
            db.init_db()
            logger.debug("Database initialized at %s", config.config.database.path)
            
            # Ensure data directories exist
            for dir_path in ["data/raw", "data/processed", "data/output", "logs"]:
                Path(dir_path).mkdir(parents=True, exist_ok=True)
            logger.debug("Data directories created")
        
        console.print(Panel.fit(
            "[green]OK[/green] Database initialized\n"
            "[green]OK[/green] Data directories created\n"
            f"[green]OK[/green] Config loaded from config.yaml\n\n"
            f"Database: [cyan]{config.config.database.path}[/cyan]",
            title="[bold]Review Miner Initialized[/bold]",
            border_style="green",
        ))
        logger.info("Initialization complete")
        
    except (ConfigError, DatabaseError) as e:
        logger.error("Initialization failed: %s", e, exc_info=True)
        console.print(Panel(f"[red]Error:[/red] {e}", title="Initialization Failed", border_style="red"))
        raise typer.Exit(1)


# ============== Import Command ==============


@app.command("import")
def import_reviews(
    file_path: str = typer.Argument(..., help="Path to CSV or JSON file to import"),
    source: str = typer.Option("manual", "--source", "-s", help="Source name for imported reviews"),
):
    """Import reviews from a CSV or JSON file."""
    from src.database import get_database
    from src.exceptions import DatabaseError
    from src.scrapers.csv_import import import_reviews as do_import
    
    path = Path(file_path)
    logger.info("Importing reviews from %s", path)
    
    if not path.exists():
        logger.error("File not found: %s", file_path)
        console.print(f"[red]Error:[/red] File not found: {file_path}")
        raise typer.Exit(1)
    
    try:
        with console.status(f"[bold green]Importing reviews from {path.name}..."):
            try:
                reviews = do_import(file_path, default_source=source)
            except ValueError as e:
                logger.error("Import parsing failed: %s", e)
                console.print(f"[red]Error:[/red] {e}")
                raise typer.Exit(1)
            
            if not reviews:
                logger.warning("No reviews found in file")
                console.print("[yellow]Warning:[/yellow] No reviews found in file.")
                raise typer.Exit(0)
            
            logger.debug("Parsed %d reviews from file", len(reviews))
            
            # Store in database
            db = get_database()
            db.init_db()  # Ensure DB exists
            count = db.insert_reviews_batch(reviews)
            logger.info("Inserted %d reviews into database", count)
        
        console.print(Panel.fit(
            f"[green]OK[/green] Imported [bold]{count}[/bold] reviews from [cyan]{path.name}[/cyan]\n"
            f"    Source: [cyan]{source}[/cyan]\n"
            f"    File format: [cyan]{path.suffix}[/cyan]",
            title="[bold]Import Complete[/bold]",
            border_style="green",
        ))
        
    except DatabaseError as e:
        logger.error("Database error during import: %s", e, exc_info=True)
        console.print(Panel(f"[red]Database Error:[/red] {e}", title="Import Failed", border_style="red"))
        raise typer.Exit(1)


# ============== Stats Command ==============


@app.command()
def stats(
    pain_points: bool = typer.Option(False, "--pain-points", "-p", help="Show pain point statistics"),
):
    """Show statistics about collected reviews and pain points."""
    from src.database import get_database
    
    db = get_database()
    
    if pain_points:
        # Show pain point stats
        pp_stats = db.get_pain_point_stats()
        
        if pp_stats.total_pain_points == 0:
            console.print("[yellow]No pain points extracted yet.[/yellow] Run 'analyze' first.")
            return
        
        console.print(f"\n[bold]Total Pain Points:[/bold] {pp_stats.total_pain_points}\n")
        
        # By category table
        table = Table(title="Pain Points by Category", show_header=True)
        table.add_column("Category", style="cyan")
        table.add_column("Count", justify="right", style="green")
        table.add_column("Percentage", justify="right")
        
        for category, count in pp_stats.by_category.items():
            pct = (count / pp_stats.total_pain_points) * 100
            table.add_row(category, str(count), f"{pct:.1f}%")
        
        console.print(table)
        
        # By intensity table
        console.print()
        table2 = Table(title="Pain Points by Emotional Intensity", show_header=True)
        table2.add_column("Intensity", style="cyan")
        table2.add_column("Count", justify="right", style="green")
        
        for intensity, count in pp_stats.by_intensity.items():
            table2.add_row(intensity, str(count))
        
        console.print(table2)
    else:
        # Show review stats
        review_stats = db.get_review_stats()
        
        if review_stats.total_reviews == 0:
            console.print("[yellow]No reviews in database.[/yellow] Run 'import' or 'scrape' first.")
            return
        
        console.print(f"\n[bold]Total Reviews:[/bold] {review_stats.total_reviews}")
        console.print(f"[bold]Processed:[/bold] {review_stats.processed_count}")
        console.print(f"[bold]Unprocessed:[/bold] {review_stats.unprocessed_count}\n")
        
        # By source table
        table = Table(title="Reviews by Source", show_header=True)
        table.add_column("Source", style="cyan")
        table.add_column("Count", justify="right", style="green")
        table.add_column("Percentage", justify="right")
        
        for source, count in review_stats.by_source.items():
            pct = (count / review_stats.total_reviews) * 100
            table.add_row(source, str(count), f"{pct:.1f}%")
        
        console.print(table)


# ============== Analyze Command ==============


@app.command()
def analyze(
    source: Optional[str] = typer.Option(None, "--source", "-s", help="Analyze only reviews from this source"),
    unprocessed: bool = typer.Option(False, "--unprocessed", "-u", help="Analyze only unprocessed reviews"),
    all_reviews: bool = typer.Option(False, "--all", "-a", help="Re-analyze all reviews"),
    batch_size: int = typer.Option(20, "--batch-size", "-b", help="Reviews per API call"),
):
    """Analyze collected reviews and extract pain points using Claude."""
    from src.analyzer import PainPointAnalyzer
    from src.config import get_config
    from src.database import get_database
    from src.exceptions import AnalyzerError, ConfigError, DatabaseError
    
    logger.info("Starting analysis (source=%s, batch_size=%d)", source, batch_size)
    
    try:
        config = get_config()
        db = get_database()
    except (ConfigError, DatabaseError) as e:
        logger.error("Failed to initialize: %s", e)
        console.print(Panel(f"[red]Error:[/red] {e}", title="Initialization Failed", border_style="red"))
        raise typer.Exit(1)
    
    # Get reviews to process
    if all_reviews:
        reviews = db.get_reviews(source=source)
    elif unprocessed:
        reviews = db.get_unprocessed_reviews()
        if source:
            reviews = [r for r in reviews if r.source == source]
    else:
        reviews = db.get_reviews(source=source, processed=False)
    
    if not reviews:
        logger.info("No reviews to analyze")
        console.print("[yellow]No reviews to analyze.[/yellow]")
        return
    
    logger.info("Found %d reviews to analyze", len(reviews))
    console.print(f"[bold]Analyzing {len(reviews)} reviews...[/bold]\n")
    
    try:
        analyzer = PainPointAnalyzer(config.anthropic_api_key)
    except ValueError as e:
        logger.error("API key error: %s", e)
        console.print(f"[red]Error:[/red] {e}")
        console.print("[dim]Set ANTHROPIC_API_KEY in your .env file[/dim]")
        raise typer.Exit(1)
    
    try:
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console,
        ) as progress:
            task = progress.add_task("Processing...", total=len(reviews))
            
            # Process in batches
            all_pain_points = []
            failed_batches = 0
            review_id_map = {i: r.id for i, r in enumerate(reviews)}
            
            for i in range(0, len(reviews), batch_size):
                batch = reviews[i:i + batch_size]
                batch_num = i // batch_size + 1
                progress.update(task, description=f"Processing batch {batch_num}...")
                logger.debug("Processing batch %d (%d reviews)", batch_num, len(batch))
                
                try:
                    pain_points = analyzer.analyze_batch_sync(batch, batch_size=len(batch))
                    logger.debug("Batch %d extracted %d pain points", batch_num, len(pain_points))
                except AnalyzerError as e:
                    logger.warning("Batch %d failed: %s", batch_num, e)
                    failed_batches += 1
                    progress.update(task, advance=len(batch))
                    continue
                
                # Map pain points to review IDs and store
                for pp in pain_points:
                    # The review_number from Claude is 1-indexed within the batch
                    batch_idx = pp.review_number - 1
                    global_idx = i + batch_idx
                    if global_idx in review_id_map and review_id_map[global_idx]:
                        from src.models import EmotionalIntensity, PainPoint
                        db_pp = PainPoint(
                            review_id=review_id_map[global_idx],
                            category=pp.pain_point_category,
                            verbatim_quote=pp.verbatim_quote,
                            emotional_intensity=EmotionalIntensity(pp.emotional_intensity.lower()),
                            implied_need=pp.implied_need,
                        )
                        db.insert_pain_point(db_pp)
                        all_pain_points.append(db_pp)
                
                progress.update(task, advance=len(batch))
            
            # Mark reviews as processed
            review_ids = [r.id for r in reviews if r.id]
            db.mark_reviews_processed(review_ids)
        
        # Build result message
        result_msg = (
            f"[green]OK[/green] Analyzed [bold]{len(reviews)}[/bold] reviews\n"
            f"[green]OK[/green] Extracted [bold]{len(all_pain_points)}[/bold] pain points"
        )
        if failed_batches > 0:
            result_msg += f"\n[yellow]Warning:[/yellow] {failed_batches} batch(es) failed"
            logger.warning("Analysis completed with %d failed batches", failed_batches)
        
        console.print(Panel.fit(result_msg, title="[bold]Analysis Complete[/bold]", border_style="green"))
        logger.info("Analysis complete: %d pain points from %d reviews", len(all_pain_points), len(reviews))
        
    except AnalyzerError as e:
        logger.error("Analysis failed: %s", e, exc_info=True)
        console.print(Panel(f"[red]Error:[/red] {e}", title="Analysis Failed", border_style="red"))
        raise typer.Exit(1)


# ============== Export Command ==============


@app.command()
def export(
    format: str = typer.Argument(..., help="Output format: csv, markdown, json"),
    output_path: str = typer.Argument(..., help="Output file path"),
    category: Optional[str] = typer.Option(None, "--category", "-c", help="Filter by category"),
):
    """Export extracted pain points to a file."""
    from src.exporter import Exporter
    
    format_lower = format.lower()
    if format_lower not in ("csv", "markdown", "md", "json"):
        console.print(f"[red]Error:[/red] Unsupported format '{format}'. Use: csv, markdown, json")
        raise typer.Exit(1)
    
    if format_lower == "md":
        format_lower = "markdown"
    
    with console.status(f"[bold green]Exporting to {output_path}..."):
        exporter = Exporter()
        
        if format_lower == "csv":
            count = exporter.to_csv(output_path, category=category)
        elif format_lower == "markdown":
            count = exporter.to_markdown(output_path, category=category)
        else:
            count = exporter.to_json(output_path, category=category)
    
    if count == 0:
        console.print("[yellow]No pain points to export.[/yellow] Run 'analyze' first.")
        return
    
    console.print(Panel.fit(
        f"[green]OK[/green] Exported [bold]{count}[/bold] pain points to [cyan]{output_path}[/cyan]",
        title="[bold]Export Complete[/bold]",
        border_style="green",
    ))


# ============== Scrape Commands ==============


@scrape_app.command("amazon")
def scrape_amazon(
    query: str = typer.Argument(..., help="Search query or product URL"),
    max_products: int = typer.Option(10, "--max-products", "-p", help="Maximum products to scrape"),
    max_reviews: int = typer.Option(50, "--max-reviews", "-r", help="Maximum reviews per product"),
):
    """Scrape reviews from Amazon."""
    import asyncio
    from src.scrapers import get_amazon_scraper
    from src.database import get_database
    from src.exceptions import ScraperError
    
    logger.info("Starting Amazon scrape for '%s'", query)
    
    AmazonScraper = get_amazon_scraper()
    
    db = get_database()
    db.init_db()
    
    async def run():
        scraper = AmazonScraper()
        try:
            with console.status(f"[bold green]Scraping Amazon for '{query}'..."):
                if query.startswith("http"):
                    logger.debug("Scraping single URL: %s", query)
                    reviews = await scraper.scrape_reviews(query, max_reviews=max_reviews)
                else:
                    logger.debug("Searching for products: %s (max=%d)", query, max_products)
                    reviews = await scraper.scrape_from_search(query, max_products, max_reviews)
                
                if reviews:
                    count = db.insert_reviews_batch(reviews)
                    logger.info("Scraped %d reviews from Amazon", count)
                    console.print(Panel.fit(
                        f"[green]OK[/green] Scraped [bold]{count}[/bold] reviews from Amazon",
                        title="[bold]Scrape Complete[/bold]",
                        border_style="green",
                    ))
                else:
                    logger.warning("No reviews found on Amazon")
                    console.print("[yellow]No reviews found.[/yellow]")
        except ScraperError as e:
            logger.error("Amazon scrape failed: %s", e, exc_info=True)
            console.print(Panel(f"[red]Error:[/red] {e}", title="Scrape Failed", border_style="red"))
            raise typer.Exit(1)
    
    asyncio.run(run())


@scrape_app.command("goodreads")
def scrape_goodreads(
    url: str = typer.Argument(..., help="Goodreads book URL"),
    max_reviews: int = typer.Option(100, "--max-reviews", "-r", help="Maximum reviews to scrape"),
):
    """Scrape reviews from Goodreads."""
    import asyncio
    from src.scrapers import get_goodreads_scraper
    from src.database import get_database
    from src.exceptions import ScraperError
    
    logger.info("Starting Goodreads scrape for %s", url)
    
    GoodreadsScraper = get_goodreads_scraper()
    
    db = get_database()
    db.init_db()
    
    async def run():
        scraper = GoodreadsScraper()
        try:
            with console.status(f"[bold green]Scraping Goodreads..."):
                reviews = await scraper.scrape_reviews(url, max_reviews=max_reviews)
                
                if reviews:
                    count = db.insert_reviews_batch(reviews)
                    logger.info("Scraped %d reviews from Goodreads", count)
                    console.print(Panel.fit(
                        f"[green]OK[/green] Scraped [bold]{count}[/bold] reviews from Goodreads",
                        title="[bold]Scrape Complete[/bold]",
                        border_style="green",
                    ))
                else:
                    logger.warning("No reviews found on Goodreads")
                    console.print("[yellow]No reviews found.[/yellow]")
        except ScraperError as e:
            logger.error("Goodreads scrape failed: %s", e, exc_info=True)
            console.print(Panel(f"[red]Error:[/red] {e}", title="Scrape Failed", border_style="red"))
            raise typer.Exit(1)
    
    asyncio.run(run())


@scrape_app.command("reddit")
def scrape_reddit(
    query: str = typer.Argument(..., help="Search query (e.g., book title)"),
    subreddits: str = typer.Option("books,suggestmeabook", "--subreddits", "-s", help="Comma-separated subreddits"),
    max_posts: int = typer.Option(50, "--max-posts", "-p", help="Maximum posts to search"),
):
    """Scrape discussions from Reddit."""
    import asyncio
    from src.scrapers import get_reddit_scraper
    from src.database import get_database
    from src.exceptions import ScraperError
    
    logger.info("Starting Reddit scrape for '%s' in %s", query, subreddits)
    
    RedditScraper = get_reddit_scraper()
    
    db = get_database()
    db.init_db()
    
    async def run():
        scraper = RedditScraper()
        sub_list = [s.strip() for s in subreddits.split(",")]
        
        try:
            with console.status(f"[bold green]Searching Reddit for '{query}'..."):
                reviews = await scraper.search_and_scrape(query, sub_list, max_posts)
                
                if reviews:
                    count = db.insert_reviews_batch(reviews)
                    logger.info("Collected %d discussions from Reddit", count)
                    console.print(Panel.fit(
                        f"[green]OK[/green] Collected [bold]{count}[/bold] discussions from Reddit",
                        title="[bold]Scrape Complete[/bold]",
                        border_style="green",
                    ))
                else:
                    logger.warning("No relevant discussions found on Reddit")
                    console.print("[yellow]No relevant discussions found.[/yellow]")
        except ScraperError as e:
            logger.error("Reddit scrape failed: %s", e, exc_info=True)
            console.print(Panel(f"[red]Error:[/red] {e}", title="Scrape Failed", border_style="red"))
            raise typer.Exit(1)
    
    asyncio.run(run())


@scrape_app.command("librarything")
def scrape_librarything(
    url: str = typer.Argument(..., help="LibraryThing work URL"),
    max_reviews: int = typer.Option(100, "--max-reviews", "-r", help="Maximum reviews to scrape"),
):
    """Scrape reviews from LibraryThing."""
    import asyncio
    from src.scrapers import get_librarything_scraper
    from src.database import get_database
    from src.exceptions import ScraperError
    
    logger.info("Starting LibraryThing scrape for %s", url)
    
    LibraryThingScraper = get_librarything_scraper()
    
    db = get_database()
    db.init_db()
    
    async def run():
        scraper = LibraryThingScraper()
        try:
            with console.status(f"[bold green]Scraping LibraryThing..."):
                reviews = await scraper.scrape_reviews(url, max_reviews=max_reviews)
                
                if reviews:
                    count = db.insert_reviews_batch(reviews)
                    logger.info("Scraped %d reviews from LibraryThing", count)
                    console.print(Panel.fit(
                        f"[green]OK[/green] Scraped [bold]{count}[/bold] reviews from LibraryThing",
                        title="[bold]Scrape Complete[/bold]",
                        border_style="green",
                    ))
                else:
                    logger.warning("No reviews found on LibraryThing")
                    console.print("[yellow]No reviews found.[/yellow]")
        except ScraperError as e:
            logger.error("LibraryThing scrape failed: %s", e, exc_info=True)
            console.print(Panel(f"[red]Error:[/red] {e}", title="Scrape Failed", border_style="red"))
            raise typer.Exit(1)
    
    asyncio.run(run())


@scrape_app.command("all")
def scrape_all(
    query: str = typer.Argument(..., help="Search query"),
    max_products: int = typer.Option(5, "--max-products", "-p", help="Maximum products per source"),
):
    """Scrape reviews from all available sources."""
    console.print("[yellow]Scraping from all sources is not yet implemented.[/yellow]")
    console.print("Use individual scrape commands: amazon, goodreads, reddit, librarything")


# ============== DB Management Commands ==============


@db_app.command("reset")
def db_reset(
    confirm: bool = typer.Option(False, "--yes", "-y", help="Confirm reset without prompting"),
):
    """Reset the database (delete all data)."""
    from src.database import get_database
    
    if not confirm:
        confirm = typer.confirm("This will delete ALL data. Are you sure?")
    
    if not confirm:
        console.print("[yellow]Aborted.[/yellow]")
        return
    
    db = get_database()
    db.reset_db()
    
    console.print("[green]OK[/green] Database reset successfully.")


@db_app.command("backup")
def db_backup(
    output_path: Optional[str] = typer.Argument(None, help="Backup file path"),
):
    """Create a backup of the database."""
    import shutil
    from datetime import datetime
    from src.config import get_config
    
    config = get_config()
    db_path = Path(config.config.database.path)
    
    if not db_path.exists():
        console.print("[red]Error:[/red] Database file not found.")
        raise typer.Exit(1)
    
    if output_path is None:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_path = f"data/review_miner_backup_{timestamp}.db"
    
    shutil.copy2(db_path, output_path)
    console.print(f"[green]OK[/green] Database backed up to [cyan]{output_path}[/cyan]")


if __name__ == "__main__":
    app()
