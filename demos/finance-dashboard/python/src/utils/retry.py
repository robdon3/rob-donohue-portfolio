"""Simple retry helper with exponential backoff — no external deps."""

from __future__ import annotations

import time
from functools import wraps
from typing import Callable, Tuple, Type, TypeVar

from .logging_setup import get_logger

T = TypeVar("T")
logger = get_logger(__name__)


def retry_with_backoff(
    *,
    max_retries: int = 3,
    backoff_seconds: float = 1.5,
    exceptions: Tuple[Type[BaseException], ...] = (Exception,),
) -> Callable[[Callable[..., T]], Callable[..., T]]:
    """
    Decorator: retry callable on specified exceptions with exponential backoff.

    Extension point: swap for tenacity or circuit-breaker middleware in production.
    """

    def decorator(fn: Callable[..., T]) -> Callable[..., T]:
        @wraps(fn)
        def wrapper(*args, **kwargs) -> T:
            attempt = 0
            while True:
                try:
                    return fn(*args, **kwargs)
                except exceptions as exc:
                    attempt += 1
                    if attempt > max_retries:
                        logger.error(
                            "exhausted retries for %s after %s attempts: %s",
                            fn.__name__,
                            max_retries,
                            exc,
                        )
                        raise
                    sleep_for = backoff_seconds * (2 ** (attempt - 1))
                    logger.warning(
                        "retry %s/%s for %s in %.1fs — %s",
                        attempt,
                        max_retries,
                        fn.__name__,
                        sleep_for,
                        exc,
                    )
                    time.sleep(sleep_for)

        return wrapper

    return decorator
