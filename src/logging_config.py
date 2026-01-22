"""Logging configuration for Review Miner with Rich integration."""

import logging
import sys
from logging.handlers import RotatingFileHandler
from pathlib import Path
from typing import Optional

from rich.console import Console
from rich.logging import RichHandler


# Module-level logger cache
_loggers_configured = False

# Default log format for file handler
FILE_FORMAT = "%(asctime)s | %(levelname)-8s | %(name)s | %(message)s"
DATE_FORMAT = "%Y-%m-%d %H:%M:%S"


def setup_logging(
    verbose: bool = False,
    quiet: bool = False,
    log_file: Optional[str] = None,
    console: Optional[Console] = None,
) -> logging.Logger:
    """Configure logging for the application.
    
    Args:
        verbose: Enable DEBUG level logging to console
        quiet: Suppress INFO level, show only WARNING and above
        log_file: Path to log file (defaults to logs/review_miner.log)
        console: Rich console instance to use (creates new if None)
    
    Returns:
        The root logger for the application
    """
    global _loggers_configured
    
    # Determine log level
    if verbose:
        console_level = logging.DEBUG
    elif quiet:
        console_level = logging.WARNING
    else:
        console_level = logging.INFO
    
    # Get or create the root logger for our app
    root_logger = logging.getLogger("review_miner")
    
    # Only configure once
    if _loggers_configured:
        # Just update the level if already configured
        for handler in root_logger.handlers:
            if isinstance(handler, RichHandler):
                handler.setLevel(console_level)
        return root_logger
    
    root_logger.setLevel(logging.DEBUG)  # Capture all, filter at handler level
    
    # Clear any existing handlers
    root_logger.handlers.clear()
    
    # Console handler with Rich
    if console is None:
        console = Console(stderr=True)
    
    rich_handler = RichHandler(
        console=console,
        show_time=True,
        show_path=False,
        rich_tracebacks=True,
        tracebacks_show_locals=verbose,
        markup=True,
    )
    rich_handler.setLevel(console_level)
    rich_handler.setFormatter(logging.Formatter("%(message)s"))
    root_logger.addHandler(rich_handler)
    
    # File handler with rotation
    log_path = Path(log_file) if log_file else Path("logs/review_miner.log")
    log_path.parent.mkdir(parents=True, exist_ok=True)
    
    file_handler = RotatingFileHandler(
        log_path,
        maxBytes=5 * 1024 * 1024,  # 5 MB
        backupCount=3,
        encoding="utf-8",
    )
    file_handler.setLevel(logging.DEBUG)  # Always log everything to file
    file_handler.setFormatter(logging.Formatter(FILE_FORMAT, DATE_FORMAT))
    root_logger.addHandler(file_handler)
    
    # Prevent propagation to root logger
    root_logger.propagate = False
    
    _loggers_configured = True
    
    # Log startup
    root_logger.debug("Logging initialized (verbose=%s, quiet=%s)", verbose, quiet)
    
    return root_logger


def get_logger(name: str) -> logging.Logger:
    """Get a logger for a specific module.
    
    Args:
        name: Module name (typically __name__)
    
    Returns:
        Logger instance for the module
    
    Example:
        logger = get_logger(__name__)
        logger.info("Starting scraper")
    """
    # Ensure logging is set up with defaults if not already
    global _loggers_configured
    if not _loggers_configured:
        setup_logging()
    
    # Create child logger under our namespace
    if name.startswith("src."):
        logger_name = f"review_miner.{name[4:]}"
    elif name == "__main__":
        logger_name = "review_miner.cli"
    else:
        logger_name = f"review_miner.{name}"
    
    return logging.getLogger(logger_name)


def reset_logging() -> None:
    """Reset logging configuration. Useful for testing."""
    global _loggers_configured
    root_logger = logging.getLogger("review_miner")
    root_logger.handlers.clear()
    _loggers_configured = False
