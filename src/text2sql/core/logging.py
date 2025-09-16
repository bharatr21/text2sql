"""
Structured logging configuration using structlog.
"""

import logging
import sys
from typing import Any, Dict

import structlog
from structlog.stdlib import LoggerFactory


def configure_logging(log_level: str = "INFO", debug: bool = False) -> None:
    """Configure structured logging."""

    # Configure standard library logging
    logging.basicConfig(
        format="%(message)s",
        stream=sys.stdout,
        level=getattr(logging, log_level.upper()),
    )

    # Configure structlog
    processors = [
        structlog.stdlib.filter_by_level,
        structlog.stdlib.add_logger_name,
        structlog.stdlib.add_log_level,
        structlog.stdlib.PositionalArgumentsFormatter(),
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
        structlog.processors.UnicodeDecoder(),
    ]

    if debug:
        # Pretty console output for development
        processors.append(structlog.dev.ConsoleRenderer())
    else:
        # JSON output for production
        processors.append(structlog.processors.JSONRenderer())

    structlog.configure(
        processors=processors,
        wrapper_class=structlog.stdlib.BoundLogger,
        logger_factory=LoggerFactory(),
        cache_logger_on_first_use=True,
    )


def get_logger(name: str) -> structlog.BoundLogger:
    """Get a structured logger instance."""
    return structlog.get_logger(name)


class LoggerMixin:
    """Mixin class to add logging to any class."""

    @property
    def logger(self) -> structlog.BoundLogger:
        """Get a logger instance for this class."""
        return get_logger(self.__class__.__name__)