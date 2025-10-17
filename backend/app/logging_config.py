"""
Structured logging configuration using structlog.

This module configures structured logging for the Thurup backend with:
- JSON output for production (machine-readable)
- Pretty console output for development (human-readable)
- Automatic context injection (timestamps, log levels, request IDs)
- Thread-safe operation for async FastAPI
"""

import logging
import sys
from typing import Any

import structlog
from structlog.types import EventDict, Processor


def add_app_context(logger: Any, method_name: str, event_dict: EventDict) -> EventDict:
    """
    Add application-specific context to all log entries.
    This processor runs for every log call.
    """
    # Add application name for log aggregation
    event_dict["app"] = "thurup-backend"
    return event_dict


def configure_logging(json_logs: bool = False, log_level: str = "INFO") -> None:
    """
    Configure structlog for the application.

    Args:
        json_logs: If True, output JSON logs (production). If False, pretty console logs (development).
        log_level: Minimum log level (DEBUG, INFO, WARNING, ERROR, CRITICAL).
    """
    # Convert log level string to logging constant
    numeric_level = getattr(logging, log_level.upper(), logging.INFO)

    # Configure standard library logging (used by uvicorn, etc.)
    logging.basicConfig(
        format="%(message)s",
        stream=sys.stdout,
        level=numeric_level,
    )

    # Define processors chain
    processors: list[Processor] = [
        # Add log level to event dict
        structlog.stdlib.add_log_level,
        # Add logger name
        structlog.stdlib.add_logger_name,
        # Add timestamp
        structlog.processors.TimeStamper(fmt="iso"),
        # Add application context
        add_app_context,
        # Add stack info for exceptions
        structlog.processors.StackInfoRenderer(),
        # Format exceptions
        structlog.processors.format_exc_info,
        # Decode unicode
        structlog.processors.UnicodeDecoder(),
    ]

    if json_logs:
        # Production: JSON output
        processors.append(structlog.processors.JSONRenderer())
    else:
        # Development: Pretty console output with colors
        processors.append(structlog.dev.ConsoleRenderer(colors=True))

    # Configure structlog
    structlog.configure(
        processors=processors,
        wrapper_class=structlog.stdlib.BoundLogger,
        context_class=dict,
        logger_factory=structlog.stdlib.LoggerFactory(),
        cache_logger_on_first_use=True,
    )


def get_logger(name: str = __name__) -> structlog.stdlib.BoundLogger:
    """
    Get a configured logger instance.

    Args:
        name: Logger name (typically __name__ of calling module).

    Returns:
        Configured structlog logger.

    Example:
        logger = get_logger(__name__)
        logger.info("player_joined", game_id=game_id, player_name=name, seat=seat)
    """
    return structlog.get_logger(name)


# Context manager for request-scoped logging
class LogContext:
    """
    Context manager for adding temporary context to logs.

    Example:
        with LogContext(game_id="abc123", seat=0):
            logger.info("bid_placed", value=16)
            # Logs will include game_id and seat automatically
    """

    def __init__(self, **kwargs: Any):
        self.context = kwargs
        self.token: Any = None

    def __enter__(self) -> "LogContext":
        self.token = structlog.contextvars.bind_contextvars(**self.context)
        return self

    def __exit__(self, *args: Any) -> None:
        if self.token is not None:
            structlog.contextvars.unbind_contextvars(*self.context.keys())
