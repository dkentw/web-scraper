"""Shared helpers: logging setup and retry decorator."""

import logging
import time
from functools import wraps

from scraper.config import MAX_RETRIES, RETRY_DELAY


def get_logger(name: str) -> logging.Logger:
    logger = logging.getLogger(name)
    if not logger.handlers:
        handler = logging.StreamHandler()
        handler.setFormatter(
            logging.Formatter("%(asctime)s [%(levelname)s] %(name)s: %(message)s")
        )
        logger.addHandler(handler)
        logger.setLevel(logging.INFO)
    return logger


def retry(max_attempts: int = MAX_RETRIES, delay: float = RETRY_DELAY):
    """Retry decorator with exponential backoff."""

    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            last_exc = None
            for attempt in range(1, max_attempts + 1):
                try:
                    return func(*args, **kwargs)
                except Exception as exc:
                    last_exc = exc
                    if attempt < max_attempts:
                        wait = delay * (2 ** (attempt - 1))
                        logging.getLogger(func.__module__).warning(
                            "Attempt %d/%d failed: %s. Retrying in %.1fs...",
                            attempt,
                            max_attempts,
                            exc,
                            wait,
                        )
                        time.sleep(wait)
            raise last_exc

        return wrapper

    return decorator
