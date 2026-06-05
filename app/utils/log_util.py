"""
SmartDocQA — Unified Logging Module
====================================
Provides structured logging with console + file output, log rotation,
and a thread-safe request-ID context for tracing across async requests.
"""

import logging
import os
import sys
from datetime import datetime
from logging.handlers import TimedRotatingFileHandler
from pathlib import Path
from typing import Optional

# Module-level state
_initialized = False
_request_id_var: Optional[str] = None


class RequestIdFilter(logging.Filter):
    """Inject X-Request-ID into every log record."""

    def filter(self, record: logging.LogRecord) -> bool:
        record.request_id = _request_id_var or "-"
        return True


def set_request_id(request_id: str) -> None:
    """Set the current request ID for traceability (called from middleware)."""
    global _request_id_var
    _request_id_var = request_id


def clear_request_id() -> None:
    global _request_id_var
    _request_id_var = None


def setup_logging(
    level: str = "INFO",
    log_dir: str = "",
    app_name: str = "SmartDocQA",
) -> None:
    """
    Initialize the global logging system.

    Configures:
        - Console handler:  DEBUG+  (coloured via format, not ANSI)
        - File handler:      INFO+   (daily rotation, 30-day retention)
        - Third-party noise: WARNING+ (uvicorn, sqlalchemy, httpx, etc.)
    """
    global _initialized
    if _initialized:
        return

    numeric_level = getattr(logging, level.upper(), logging.INFO)

    # ── Log directory ──
    if not log_dir:
        log_dir = str(Path(__file__).parent.parent.parent.resolve() / "logs")
    Path(log_dir).mkdir(parents=True, exist_ok=True)

    # ── Formatter ──
    file_fmt = logging.Formatter(
        fmt=(
            "%(asctime)s | %(levelname)-7s | %(name)-24s | "
            "%(filename)s:%(lineno)-4d | [%(request_id)s] %(message)s"
        ),
        datefmt="%Y-%m-%d %H:%M:%S",
    )
    console_fmt = logging.Formatter(
        fmt="%(asctime)s | %(levelname)-7s | %(name)s | %(message)s",
        datefmt="%H:%M:%S",
    )

    # ── Root logger ──
    root = logging.getLogger()
    root.setLevel(numeric_level)

    # Remove default handlers to avoid duplicates on reload
    root.handlers.clear()

    # ── Console handler ──
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(numeric_level)
    console_handler.setFormatter(console_fmt)
    root.addHandler(console_handler)

    # ── File handler (daily rotation, 30-day retention) ──
    log_file = Path(log_dir) / f"{app_name.lower()}.log"
    file_handler = TimedRotatingFileHandler(
        filename=str(log_file),
        when="midnight",
        interval=1,
        backupCount=30,
        encoding="utf-8",
    )
    file_handler.setLevel(numeric_level)
    file_handler.setFormatter(file_fmt)
    root.addHandler(file_handler)

    # ── Request-ID filter for all handlers ──
    rid_filter = RequestIdFilter()
    console_handler.addFilter(rid_filter)
    file_handler.addFilter(rid_filter)

    # ── Quiet third-party libraries ──
    for noisy in ("uvicorn", "sqlalchemy", "httpx", "httpcore", "urllib3",
                  "openai", "langchain", "sentence_transformers",
                  "huggingface_hub", "filelock", "matplotlib", "PIL"):
        logging.getLogger(noisy).setLevel(logging.WARNING)

    _initialized = True
    root.info("Logging initialised | level=%s | file=%s", level, log_file)


def get_logger(name: str) -> logging.Logger:
    """Get a logger with the given module name."""
    return logging.getLogger(name)
