"""
Structured Logging Module.

Provides a centralized logger for all modules with consistent formatting,
debug info, and optional file persistence.
"""

import logging
import sys
from pathlib import Path
from typing import Optional

# Log format with timestamp, level, module, and message
LOG_FORMAT = "%(asctime)s [%(levelname)s] %(name)s: %(message)s"
LOG_DATE_FORMAT = "%Y-%m-%d %H:%M:%S"

# Map of logger instances to avoid recreating them
_loggers = {}


def get_logger(name: str, level: str = "INFO", log_file: Optional[str] = None) -> logging.Logger:
    """
    Get or create a logger instance.
    
    Args:
        name: Logger name (typically __name__)
        level: Log level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        log_file: Optional path to log file for persistence
    
    Returns:
        Configured logger instance
    """
    # Return cached logger if exists
    if name in _loggers:
        return _loggers[name]
    
    logger = logging.getLogger(name)
    logger.setLevel(getattr(logging, level.upper()))
    
    # Console handler (always add)
    if not logger.handlers:
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(getattr(logging, level.upper()))
        formatter = logging.Formatter(LOG_FORMAT, datefmt=LOG_DATE_FORMAT)
        console_handler.setFormatter(formatter)
        logger.addHandler(console_handler)
        
        # File handler (optional)
        if log_file:
            log_path = Path(log_file)
            log_path.parent.mkdir(parents=True, exist_ok=True)
            file_handler = logging.FileHandler(log_path)
            file_handler.setLevel(getattr(logging, level.upper()))
            file_handler.setFormatter(formatter)
            logger.addHandler(file_handler)
    
    _loggers[name] = logger
    return logger


def set_global_level(level: str) -> None:
    """Set log level for all existing loggers."""
    log_level = getattr(logging, level.upper())
    for logger in _loggers.values():
        logger.setLevel(log_level)
        for handler in logger.handlers:
            handler.setLevel(log_level)
