import asyncio
import functools
import random
from typing import Callable, Any, Tuple, Type
from src.utils.logging import logger

def async_retry(
    max_retries: int = 3,
    base_delay: float = 1.0,
    max_delay: float = 30.0,
    backoff_factor: float = 2.0,
    exceptions: Tuple[Type[Exception], ...] = (Exception,)
) -> Callable:
    """
    Decorator for retrying asynchronous coroutines with exponential backoff and jitter.
    """
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        async def wrapper(*args: Any, **kwargs: Any) -> Any:
            retries = 0
            delay = base_delay
            while True:
                try:
                    return await func(*args, **kwargs)
                except exceptions as e:
                    retries += 1
                    if retries > max_retries:
                        logger.error(
                            f"Function '{func.__name__}' failed after {max_retries} retries: {str(e)}"
                        )
                        raise
                    jitter = random.uniform(0.8, 1.2)
                    current_delay = min(delay * jitter, max_delay)
                    logger.warning(
                        f"Attempt {retries}/{max_retries} for '{func.__name__}' failed: {e}. "
                        f"Retrying in {current_delay:.2f}s..."
                    )
                    await asyncio.sleep(current_delay)
                    delay *= backoff_factor
        return wrapper
    return decorator

