"""
app/core/logging.py — Structured Logging Configuration

PATTERN: Structured JSON logging for production, human-readable for development.

WHY structured logging (JSON in production):
    - Log aggregation tools (Datadog, ELK Stack, AWS CloudWatch Logs Insights)
      parse JSON logs natively. Searching for all errors from a specific
      user_id or request_id requires structured fields, not regex on plain text.
    - Correlation IDs: Every log line for a single request shares the same
      request_id. Enables full request tracing in distributed logs.
    - Machine-readable: Alert rules can be set on specific JSON fields
      (e.g., alert when error.code == "INSUFFICIENT_STOCK" > 10/minute).

WHY NOT:
    - Python's default logging format: Unstructured. No request correlation.
    - Loguru: Excellent library but adds a dependency for something Python's
      stdlib handles adequately with configuration.
    - structlog: Powerful but adds complexity. Standard logging + JSON formatter
      achieves 90% of the benefit.

SECURITY:
    - Sensitive data (passwords, tokens) must NEVER appear in logs.
    - User email is included for debugging but should be masked in strict
      compliance environments (replace with user_id).
    - Log level WARNING+ should trigger alerts in production.
"""

from __future__ import annotations

import logging
import logging.config
import sys
from typing import Any

import orjson

from app.core.config import get_settings


class JSONFormatter(logging.Formatter):
    """
    Formats log records as JSON for production consumption.

    Each log line is a valid JSON object — one per line (JSONL format).
    This is the standard format for CloudWatch, Datadog, and ELK.
    """

    def format(self, record: logging.LogRecord) -> str:
        log_entry: dict[str, Any] = {
            "timestamp": self.formatTime(record, datefmt="%Y-%m-%dT%H:%M:%S.%fZ"),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno,
        }

        # Include exception info if present
        if record.exc_info:
            log_entry["exception"] = self.formatException(record.exc_info)

        # Include extra fields attached to the log record
        # (e.g., request_id, user_id added via LoggerAdapter)
        for key in ("request_id", "user_id", "user_role", "path", "method"):
            value = getattr(record, key, None)
            if value is not None:
                log_entry[key] = value

        return orjson.dumps(log_entry).decode("utf-8")


def configure_logging() -> None:
    """
    Configure application-wide logging.

    Development: Human-readable colored output to stdout.
    Production: JSON output to stdout (captured by container log driver).

    WHY stdout (not file):
        In containerized environments, stdout/stderr are captured by the
        container runtime (Docker, Kubernetes) and forwarded to the configured
        log driver (CloudWatch, Fluentd, etc.). Writing to files inside a
        container requires volume mounts and is harder to aggregate.
    """
    settings = get_settings()

    if settings.is_production:
        handler: logging.Handler = logging.StreamHandler(sys.stdout)
        handler.setFormatter(JSONFormatter())
        formatter_name = "json"
    else:
        handler = logging.StreamHandler(sys.stdout)
        handler.setFormatter(
            logging.Formatter(
                fmt="%(asctime)s | %(levelname)-8s | %(name)s:%(lineno)d | %(message)s",
                datefmt="%H:%M:%S",
            )
        )

    logging.basicConfig(
        level=getattr(logging, settings.log_level),
        handlers=[handler],
        force=True,
    )

    # Reduce noise from verbose third-party libraries
    logging.getLogger("sqlalchemy.engine").setLevel(logging.WARNING)
    logging.getLogger("sqlalchemy.pool").setLevel(logging.WARNING)
    logging.getLogger("celery").setLevel(logging.INFO)
    logging.getLogger("uvicorn.access").setLevel(logging.WARNING)

    logger = logging.getLogger(__name__)
    logger.info(
        "Logging configured | env=%s | level=%s",
        settings.app_env,
        settings.log_level,
    )
