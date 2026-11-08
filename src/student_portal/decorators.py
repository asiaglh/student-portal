"""Декоратори застосунку."""

import functools
import logging
import time
from collections.abc import Callable

logger = logging.getLogger(__name__)


def timed[**P, R](func: Callable[P, R]) -> Callable[P, R]:
    """Записує в журнал час виконання, зокрема при винятку."""

    @functools.wraps(func)
    def wrapper(*args: P.args, **kwargs: P.kwargs) -> R:
        start = time.perf_counter()
        try:
            return func(*args, **kwargs)
        finally:
            elapsed = time.perf_counter() - start
            logger.info("%s: %.1f мс", func.__qualname__, elapsed * 1000)

    return wrapper
