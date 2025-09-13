"""Enhanced logging configuration with rotation and multiple handlers."""

from __future__ import annotations

import json
import logging
import logging.handlers
import os
import sys
from datetime import datetime
from logging import Logger
from pathlib import Path
from typing import Any, Dict, Optional


class ColoredFormatter(logging.Formatter):
    """Custom formatter with color support for console output."""
    
    # ANSI color codes
    COLORS = {
        'DEBUG': '\033[36m',     # Cyan
        'INFO': '\033[32m',      # Green
        'WARNING': '\033[33m',   # Yellow
        'ERROR': '\033[31m',     # Red
        'CRITICAL': '\033[35m',  # Magenta
    }
    RESET = '\033[0m'
    
    def format(self, record: logging.LogRecord) -> str:
        """Format log record with colors."""
        if not sys.stdout.isatty():
            # No colors if not a terminal
            return super().format(record)
        
        # Add color to level name
        levelname = record.levelname
        if levelname in self.COLORS:
            record.levelname = f"{self.COLORS[levelname]}{levelname}{self.RESET}"
        
        # Format the message
        result = super().format(record)
        
        # Reset levelname for other handlers
        record.levelname = levelname
        
        return result


class JSONFormatter(logging.Formatter):
    """JSON formatter for structured logging."""
    
    def format(self, record: logging.LogRecord) -> str:
        """Format log record as JSON."""
        log_data = {
            'timestamp': datetime.fromtimestamp(record.created).isoformat(),
            'level': record.levelname,
            'logger': record.name,
            'message': record.getMessage(),
            'module': record.module,
            'function': record.funcName,
            'line': record.lineno,
        }
        
        # Add exception info if present
        if record.exc_info:
            log_data['exception'] = self.formatException(record.exc_info)
        
        # Add extra fields
        for key, value in record.__dict__.items():
            if key not in ['name', 'msg', 'args', 'created', 'filename',
                          'funcName', 'levelname', 'lineno', 'module',
                          'msecs', 'message', 'pathname', 'process',
                          'processName', 'thread', 'threadName', 'exc_info',
                          'exc_text', 'stack_info', 'levelno', 'relativeCreated']:
                log_data[key] = value
        
        return json.dumps(log_data)


def setup_logging(
    log_level: Optional[str] = None,
    log_file: Optional[str] = None,
    logs_dir: Optional[Path] = None,
    console: bool = True,
    json_format: bool = False,
    debug: bool = False,
) -> None:
    """Set up comprehensive logging configuration.
    
    Args:
        log_level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        log_file: Path to log file
        logs_dir: Directory for log files
        console: Whether to log to console
        json_format: Use JSON format for logs
        debug: Enable debug mode
    """
    # Determine log level
    if log_level is None:
        log_level = os.getenv("LOG_LEVEL", "INFO")
        if debug or os.getenv("DEBUG", "false").lower() == "true":
            log_level = "DEBUG"
    
    # Convert to logging constant
    level = getattr(logging, log_level.upper(), logging.INFO)
    
    # Create logs directory if needed
    if logs_dir is None:
        logs_dir = Path("logs")
    logs_dir.mkdir(parents=True, exist_ok=True)
    
    # Clear existing handlers
    root_logger = logging.getLogger()
    root_logger.handlers.clear()
    root_logger.setLevel(level)
    
    # Console handler
    if console:
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(level)
        
        if json_format:
            console_formatter = JSONFormatter()
        else:
            if sys.stdout.isatty():
                # Use colored formatter for terminal
                console_formatter = ColoredFormatter(
                    '%(asctime)s | %(levelname)s | %(name)s | %(message)s',
                    datefmt='%Y-%m-%d %H:%M:%S'
                )
            else:
                console_formatter = logging.Formatter(
                    '%(asctime)s | %(levelname)s | %(name)s | %(message)s',
                    datefmt='%Y-%m-%d %H:%M:%S'
                )
        
        console_handler.setFormatter(console_formatter)
        root_logger.addHandler(console_handler)
    
    # File handler with rotation
    if log_file is None:
        log_file = logs_dir / f"yt_faceless_{datetime.now().strftime('%Y%m%d')}.log"
    else:
        log_file = Path(log_file)
    
    # Rotating file handler
    max_bytes = int(os.getenv("LOG_MAX_SIZE_MB", "100")) * 1024 * 1024
    backup_count = int(os.getenv("LOG_RETENTION_DAYS", "30"))
    
    file_handler = logging.handlers.RotatingFileHandler(
        log_file,
        maxBytes=max_bytes,
        backupCount=backup_count,
        encoding='utf-8'
    )
    file_handler.setLevel(level)
    
    if json_format:
        file_formatter = JSONFormatter()
    else:
        file_formatter = logging.Formatter(
            '%(asctime)s | %(levelname)s | %(name)s | [%(filename)s:%(lineno)d] | %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
    
    file_handler.setFormatter(file_formatter)
    root_logger.addHandler(file_handler)
    
    # Error file handler (ERROR and above)
    error_file = logs_dir / f"yt_faceless_errors_{datetime.now().strftime('%Y%m%d')}.log"
    error_handler = logging.handlers.RotatingFileHandler(
        error_file,
        maxBytes=max_bytes,
        backupCount=backup_count,
        encoding='utf-8'
    )
    error_handler.setLevel(logging.ERROR)
    error_handler.setFormatter(file_formatter)
    root_logger.addHandler(error_handler)
    
    # Configure third-party loggers
    logging.getLogger('urllib3').setLevel(logging.WARNING)
    logging.getLogger('requests').setLevel(logging.WARNING)
    logging.getLogger('aiohttp').setLevel(logging.WARNING)
    
    # Log initial message
    logger = logging.getLogger(__name__)
    logger.info(f"Logging configured - Level: {log_level}, File: {log_file}")


def get_logger(name: str) -> Logger:
    """Create or retrieve a configured logger.

    Args:
        name: Logger name (usually __name__).

    Returns:
        A configured Logger instance with INFO level and a concise format.
    """
    logger = logging.getLogger(name)
    if not logger.handlers:
        handler = logging.StreamHandler()
        formatter = logging.Formatter(
            fmt="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
        )
        handler.setFormatter(formatter)
        logger.addHandler(handler)
        logger.setLevel(logging.INFO)
        logger.propagate = False
    return logger


class LogContext:
    """Context manager for adding context to log messages."""
    
    def __init__(self, logger: Logger, **context):
        self.logger = logger
        self.context = context
        self.old_context = {}
    
    def __enter__(self):
        """Enter context and add context to logger."""
        for key, value in self.context.items():
            if hasattr(self.logger, key):
                self.old_context[key] = getattr(self.logger, key)
            setattr(self.logger, key, value)
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Exit context and restore logger state."""
        for key in self.context:
            if key in self.old_context:
                setattr(self.logger, key, self.old_context[key])
            else:
                delattr(self.logger, key)


def log_performance(func):
    """Decorator to log function performance."""
    import functools
    import time
    
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        logger = get_logger(func.__module__)
        start_time = time.time()
        
        try:
            result = func(*args, **kwargs)
            elapsed = time.time() - start_time
            logger.debug(
                f"{func.__name__} completed in {elapsed:.3f}s",
                extra={'duration': elapsed, 'function': func.__name__}
            )
            return result
            
        except Exception as e:
            elapsed = time.time() - start_time
            logger.error(
                f"{func.__name__} failed after {elapsed:.3f}s: {e}",
                extra={'duration': elapsed, 'function': func.__name__}
            )
            raise
    
    return wrapper


def log_async_performance(func):
    """Decorator to log async function performance."""
    import functools
    import time
    import asyncio
    
    @functools.wraps(func)
    async def wrapper(*args, **kwargs):
        logger = get_logger(func.__module__)
        start_time = time.time()
        
        try:
            result = await func(*args, **kwargs)
            elapsed = time.time() - start_time
            logger.debug(
                f"{func.__name__} completed in {elapsed:.3f}s",
                extra={'duration': elapsed, 'function': func.__name__}
            )
            return result
            
        except Exception as e:
            elapsed = time.time() - start_time
            logger.error(
                f"{func.__name__} failed after {elapsed:.3f}s: {e}",
                extra={'duration': elapsed, 'function': func.__name__}
            )
            raise
    
    return wrapper