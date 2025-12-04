"""
Retry Logic with Exponential Backoff.

Provides decorators for retrying failed function calls with exponential backoff
and optional jitter for distributed systems.
"""

import time
import functools
import random
from typing import Callable, Any, Type, Tuple, Optional
from src.monitoring.logger import get_logger

logger = get_logger(__name__)


def retry_with_backoff(
    max_retries: int = 3,
    base_delay: float = 1.0,
    max_delay: float = 60.0,
    exponential_base: float = 2.0,
    jitter: bool = True,
    exceptions: Tuple[Type[Exception], ...] = (Exception,),
):
    """
    Decorator for retrying functions with exponential backoff.
    
    Args:
        max_retries: Maximum number of retry attempts
        base_delay: Initial delay in seconds
        max_delay: Maximum delay cap in seconds
        exponential_base: Base for exponential backoff (delay = base_delay * exponential_base^attempt)
        jitter: Whether to add random jitter to delays
        exceptions: Tuple of exceptions to catch and retry on
    
    Returns:
        Decorated function with retry logic
    
    Example:
        @retry_with_backoff(max_retries=3, base_delay=1.0)
        def unreliable_api_call():
            ...
    """
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs) -> Any:
            attempt = 0
            last_exception = None
            
            while attempt <= max_retries:
                try:
                    return func(*args, **kwargs)
                
                except exceptions as e:
                    last_exception = e
                    attempt += 1
                    
                    if attempt > max_retries:
                        logger.error(
                            f"Function {func.__name__} failed after {max_retries} retries: {e}"
                        )
                        raise
                    
                    # Calculate delay with exponential backoff
                    delay = min(
                        base_delay * (exponential_base ** (attempt - 1)),
                        max_delay
                    )
                    
                    # Add jitter
                    if jitter:
                        delay = delay * (0.5 + random.random())
                    
                    logger.warning(
                        f"Attempt {attempt}/{max_retries} failed for {func.__name__}. "
                        f"Retrying in {delay:.2f}s: {e}"
                    )
                    
                    time.sleep(delay)
            
            raise last_exception
        
        return wrapper
    return decorator


def retry_on_exception(
    exception_type: Type[Exception] = Exception,
    max_retries: int = 3,
    delay: float = 1.0,
):
    """
    Simpler retry decorator for specific exception types.
    
    Args:
        exception_type: Exception type to catch
        max_retries: Number of retry attempts
        delay: Fixed delay between retries (no backoff)
    
    Returns:
        Decorated function
    """
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs) -> Any:
            for attempt in range(max_retries + 1):
                try:
                    return func(*args, **kwargs)
                except exception_type as e:
                    if attempt == max_retries:
                        logger.error(f"Final attempt failed: {e}")
                        raise
                    logger.warning(f"Attempt {attempt + 1} failed, retrying in {delay}s")
                    time.sleep(delay)
        
        return wrapper
    return decorator


class RetryableOperation:
    """Context manager for retryable operations."""
    
    def __init__(
        self,
        max_retries: int = 3,
        base_delay: float = 1.0,
        operation_name: str = "operation",
    ):
        """
        Initialize retryable operation context.
        
        Args:
            max_retries: Maximum retry attempts
            base_delay: Initial delay in seconds
            operation_name: Name for logging
        """
        self.max_retries = max_retries
        self.base_delay = base_delay
        self.operation_name = operation_name
        self.attempt = 0
    
    def __enter__(self):
        """Enter context manager."""
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Handle exceptions with retry logic."""
        if exc_type is None:
            return False
        
        self.attempt += 1
        if self.attempt >= self.max_retries:
            logger.error(f"{self.operation_name} failed after {self.max_retries} attempts")
            return False
        
        delay = self.base_delay * (2 ** (self.attempt - 1))
        logger.warning(f"Retrying {self.operation_name} in {delay}s (attempt {self.attempt})")
        time.sleep(delay)
        return True
