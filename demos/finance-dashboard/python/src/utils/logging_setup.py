"""Structured-ish logging for demo pipelines (production-vibe, zero deps)."""

from __future__ import annotations

import logging
import sys
from typing import Optional


_CONFIGURED = False


def setup_logging(level: str = "INFO") -> None:
    """Configure root logging once. Safe to call multiple times."""
    global _CONFIGURED
    if _CONFIGURED:
        return

    numeric = getattr(logging, level.upper(), logging.INFO)
    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(
        logging.Formatter(
            fmt="%(asctime)s | %(levelname)-7s | %(name)s | %(message)s",
            datefmt="%Y-%m-%dT%H:%M:%S",
        )
    )
    root = logging.getLogger()
    root.handlers.clear()
    root.addHandler(handler)
    root.setLevel(numeric)
    _CONFIGURED = True


def get_logger(name: Optional[str] = None) -> logging.Logger:
    """Return a named logger; ensures baseline config exists."""
    if not _CONFIGURED:
        setup_logging()
    return logging.getLogger(name or "finance_dashboard")
