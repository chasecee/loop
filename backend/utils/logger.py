"""Centralized logging utility."""

import logging
import logging.handlers
import os
import sys
from pathlib import Path
from typing import Optional


def _is_running_under_systemd() -> bool:
    """Detect if we're running under systemd (which already adds timestamps)."""
    return (
        "JOURNAL_STREAM" in os.environ or
        "INVOCATION_ID" in os.environ or 
        os.getppid() == 1  # Direct child of systemd
    )


def setup_logger(
    name: str = "loop",
    level: str = "INFO",
    log_file: Optional[Path] = None,
    max_bytes: int = 10 * 1024 * 1024,  # 10MB
    backup_count: int = 5
) -> logging.Logger:
    """Set up a logger with console and optional file output."""
    
    logger = logging.getLogger(name)
    logger.setLevel(getattr(logging, level.upper()))
    
    # Remove existing handlers to avoid duplicates
    for handler in logger.handlers[:]:
        logger.removeHandler(handler)
    
    # Detect if running under systemd (which already adds timestamps)
    under_systemd = _is_running_under_systemd()
    
    if under_systemd:
        # Systemd already adds timestamps, so use simpler format
        console_formatter = logging.Formatter('%(name)s - %(levelname)s - %(message)s')
    else:
        # Include timestamp for standalone runs
        console_formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
    
    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(console_formatter)
    logger.addHandler(console_handler)
    
    # File handler (if specified) - always include timestamp in files
    if log_file:
        log_file.parent.mkdir(parents=True, exist_ok=True)
        file_formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        file_handler = logging.handlers.RotatingFileHandler(
            log_file,
            maxBytes=max_bytes,
            backupCount=backup_count
        )
        file_handler.setFormatter(file_formatter)
        logger.addHandler(file_handler)
    
    return logger


def get_logger(name: str = "loop") -> logging.Logger:
    """Get a configured logger instance with the specified name."""
    # Check if logger already exists
    logger = logging.getLogger(name)
    
    # If it doesn't have handlers, set it up
    if not logger.handlers:
        log_dir = Path.home() / ".loop" / "logs"
        log_file = log_dir / "loop.log"
        logger = setup_logger(name, log_file=log_file)
    
    return logger


def log_exception(logger: logging.Logger, message: str = ""):
    """Log an exception with full traceback."""
    logger.exception(f"Exception occurred: {message}" if message else "Exception occurred") 