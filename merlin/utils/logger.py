from __future__ import annotations

import logging
import os
from typing import Optional

import structlog


_LOGGER: Optional[structlog.stdlib.BoundLogger] = None


def _configure_logging(level: str) -> None:
    logging.basicConfig(
        level=getattr(logging, level.upper(), logging.INFO),
        format="%(message)s",
    )

    structlog.configure(
        processors=[
            structlog.processors.add_log_level,
            structlog.processors.TimeStamper(fmt="iso"),
            structlog.processors.dict_tracebacks,
            structlog.processors.JSONRenderer(),
        ],
        wrapper_class=structlog.stdlib.BoundLogger,
        logger_factory=structlog.stdlib.LoggerFactory(),
        cache_logger_on_first_use=True,
    )


def get_logger(name: str = "merlin") -> structlog.stdlib.BoundLogger:
    """Return a configured structlog logger (singleton config)."""
    global _LOGGER
    if _LOGGER is None:
        level = os.getenv("MERLIN_LOG_LEVEL", "INFO")
        _configure_logging(level)
        _LOGGER = structlog.get_logger(name)
    return _LOGGER


