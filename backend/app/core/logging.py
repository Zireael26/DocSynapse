"""
DocSynapse Logging Configuration

This module sets up comprehensive logging for the DocSynapse application
with both file and console output, proper formatting, and log rotation.
"""

import logging
import logging.handlers
import sys
from pathlib import Path
from typing import Optional


def setup_logging(
    log_level: str = "DEBUG",
    log_file: Optional[str] = None,
    max_bytes: int = 10 * 1024 * 1024,  # 10MB
    backup_count: int = 5
) -> None:
    """
    Set up comprehensive logging for the application.

    Args:
        log_level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        log_file: Path to log file (optional)
        max_bytes: Maximum size of log file before rotation
        backup_count: Number of backup files to keep
    """

    # Create logs directory
    logs_dir = Path("logs")
    logs_dir.mkdir(exist_ok=True)

    # Configure root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(getattr(logging, log_level.upper()))

    # Clear existing handlers
    root_logger.handlers.clear()

    # Create formatter
    formatter = logging.Formatter(
        fmt="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S"
    )

    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(getattr(logging, log_level.upper()))
    console_handler.setFormatter(formatter)
    root_logger.addHandler(console_handler)

    # File handler with rotation
    if log_file is None:
        log_file = str(logs_dir / "docsynapse.log")

    file_handler = logging.handlers.RotatingFileHandler(
        log_file,
        maxBytes=max_bytes,
        backupCount=backup_count
    )
    file_handler.setLevel(logging.DEBUG)  # Always log everything to file
    file_handler.setFormatter(formatter)
    root_logger.addHandler(file_handler)

    # Configure specific loggers
    configure_component_loggers()

    # Log startup message
    logger = logging.getLogger(__name__)
    logger.info(f"Logging configured - Level: {log_level}, File: {log_file}")


def configure_component_loggers() -> None:
    """Configure loggers for specific components."""

    # Reduce noise from external libraries
    logging.getLogger("urllib3").setLevel(logging.WARNING)
    logging.getLogger("requests").setLevel(logging.WARNING)
    logging.getLogger("playwright").setLevel(logging.INFO)
    logging.getLogger("asyncio").setLevel(logging.WARNING)

    # Set specific levels for our components
    logging.getLogger("app.services.crawler").setLevel(logging.INFO)
    logging.getLogger("app.services.processor").setLevel(logging.INFO)
    logging.getLogger("app.api").setLevel(logging.INFO)


def get_logger(name: str) -> logging.Logger:
    """Get a logger for a specific component."""
    return logging.getLogger(name)
