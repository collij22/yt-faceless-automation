"""Retry utilities for resilient API calls and operations."""

from __future__ import annotations

import asyncio
import functools
import logging
import random
import time
from typing import Any, Callable, Optional, Tuple, Type, Union

from ..core.errors import (
    NonRetryableError,
    RateLimitError,
    RetryableError,
)

logger = logging.getLogger(__name__)


class RetryStrategy:
    """Base class for retry strategies."""
    
    def get_wait_time(self, attempt: int) -> float:
        """Get wait time for the given attempt number.
        
        Args:
            attempt: Attempt number (0-based)
        
        Returns:
            Wait time in seconds
        """
        raise NotImplementedError


class ExponentialBackoff(RetryStrategy):
    """Exponential backoff retry strategy."""
    
    def __init__(
        self,
        base: float = 2.0,
        max_wait: float = 60.0,
        jitter: bool = True
    ):
        self.base = base
        self.max_wait = max_wait
        self.jitter = jitter
    
    def get_wait_time(self, attempt: int) -> float:
        """Calculate wait time with exponential backoff."""
        wait_time = min(self.base ** attempt, self.max_wait)
        
        if self.jitter:
            # Add random jitter to prevent thundering herd
            wait_time *= (0.5 + random.random())
        
        return wait_time


class LinearBackoff(RetryStrategy):
    """Linear backoff retry strategy."""
    
    def __init__(
        self,
        increment: float = 1.0,
        max_wait: float = 30.0
    ):
        self.increment = increment
        self.max_wait = max_wait
    
    def get_wait_time(self, attempt: int) -> float:
        """Calculate wait time with linear backoff."""
        return min(self.increment * (attempt + 1), self.max_wait)


class FixedDelay(RetryStrategy):
    """Fixed delay retry strategy."""
    
    def __init__(self, delay: float = 1.0):
        self.delay = delay
    
    def get_wait_time(self, attempt: int) -> float:
        """Return fixed wait time."""
        return self.delay


class RetryConfig:
    """Configuration for retry behavior."""
    
    def __init__(
        self,
        max_attempts: int = 3,
        strategy: Optional[RetryStrategy] = None,
        retryable_exceptions: Optional[Tuple[Type[Exception], ...]] = None,
        non_retryable_exceptions: Optional[Tuple[Type[Exception], ...]] = None,
        on_retry: Optional[Callable] = None,
        on_failure: Optional[Callable] = None,
    ):
        self.max_attempts = max_attempts
        self.strategy = strategy or ExponentialBackoff()
        self.retryable_exceptions = retryable_exceptions or (Exception,)
        self.non_retryable_exceptions = non_retryable_exceptions or (NonRetryableError,)
        self.on_retry = on_retry
        self.on_failure = on_failure


def retry(
    max_attempts: int = 3,
    strategy: Optional[RetryStrategy] = None,
    retryable_exceptions: Optional[Tuple[Type[Exception], ...]] = None,
    non_retryable_exceptions: Optional[Tuple[Type[Exception], ...]] = None,
    on_retry: Optional[Callable] = None,
    on_failure: Optional[Callable] = None,
) -> Callable:
    """Decorator for adding retry logic to functions.
    
    Args:
        max_attempts: Maximum number of attempts
        strategy: Retry strategy to use
        retryable_exceptions: Exceptions that trigger retry
        non_retryable_exceptions: Exceptions that should not be retried
        on_retry: Callback function called on each retry
        on_failure: Callback function called on final failure
    
    Returns:
        Decorated function with retry logic
    """
    config = RetryConfig(
        max_attempts=max_attempts,
        strategy=strategy,
        retryable_exceptions=retryable_exceptions,
        non_retryable_exceptions=non_retryable_exceptions,
        on_retry=on_retry,
        on_failure=on_failure,
    )
    
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            return execute_with_retry(func, args, kwargs, config)
        
        return wrapper
    
    return decorator


def execute_with_retry(
    func: Callable,
    args: tuple,
    kwargs: dict,
    config: RetryConfig
) -> Any:
    """Execute function with retry logic.
    
    Args:
        func: Function to execute
        args: Function arguments
        kwargs: Function keyword arguments
        config: Retry configuration
    
    Returns:
        Function result
    
    Raises:
        Last exception if all retries fail
    """
    last_exception = None
    
    for attempt in range(config.max_attempts):
        try:
            return func(*args, **kwargs)
            
        except config.non_retryable_exceptions as e:
            # Don't retry these exceptions
            logger.error(f"{func.__name__} failed with non-retryable error: {e}")
            raise
            
        except RateLimitError as e:
            # Special handling for rate limits
            if attempt < config.max_attempts - 1:
                wait_time = e.retry_after if e.retry_after else config.strategy.get_wait_time(attempt)
                logger.warning(
                    f"{func.__name__} rate limited, waiting {wait_time}s "
                    f"(attempt {attempt + 1}/{config.max_attempts})"
                )
                
                if config.on_retry:
                    config.on_retry(attempt, e, wait_time)
                
                time.sleep(wait_time)
                last_exception = e
            else:
                last_exception = e
                break
                
        except config.retryable_exceptions as e:
            last_exception = e
            
            if attempt < config.max_attempts - 1:
                wait_time = config.strategy.get_wait_time(attempt)
                logger.warning(
                    f"{func.__name__} failed with {type(e).__name__}: {e}, "
                    f"retrying in {wait_time}s (attempt {attempt + 1}/{config.max_attempts})"
                )
                
                if config.on_retry:
                    config.on_retry(attempt, e, wait_time)
                
                time.sleep(wait_time)
            else:
                break
    
    # All retries failed
    logger.error(
        f"{func.__name__} failed after {config.max_attempts} attempts: {last_exception}"
    )
    
    if config.on_failure:
        config.on_failure(last_exception)
    
    raise last_exception


def async_retry(
    max_attempts: int = 3,
    strategy: Optional[RetryStrategy] = None,
    retryable_exceptions: Optional[Tuple[Type[Exception], ...]] = None,
    non_retryable_exceptions: Optional[Tuple[Type[Exception], ...]] = None,
    on_retry: Optional[Callable] = None,
    on_failure: Optional[Callable] = None,
) -> Callable:
    """Async decorator for adding retry logic to async functions.
    
    Args:
        max_attempts: Maximum number of attempts
        strategy: Retry strategy to use
        retryable_exceptions: Exceptions that trigger retry
        non_retryable_exceptions: Exceptions that should not be retried
        on_retry: Callback function called on each retry
        on_failure: Callback function called on final failure
    
    Returns:
        Decorated async function with retry logic
    """
    config = RetryConfig(
        max_attempts=max_attempts,
        strategy=strategy,
        retryable_exceptions=retryable_exceptions,
        non_retryable_exceptions=non_retryable_exceptions,
        on_retry=on_retry,
        on_failure=on_failure,
    )
    
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        async def wrapper(*args, **kwargs):
            return await async_execute_with_retry(func, args, kwargs, config)
        
        return wrapper
    
    return decorator


async def async_execute_with_retry(
    func: Callable,
    args: tuple,
    kwargs: dict,
    config: RetryConfig
) -> Any:
    """Execute async function with retry logic.
    
    Args:
        func: Async function to execute
        args: Function arguments
        kwargs: Function keyword arguments
        config: Retry configuration
    
    Returns:
        Function result
    
    Raises:
        Last exception if all retries fail
    """
    last_exception = None
    
    for attempt in range(config.max_attempts):
        try:
            return await func(*args, **kwargs)
            
        except config.non_retryable_exceptions as e:
            logger.error(f"{func.__name__} failed with non-retryable error: {e}")
            raise
            
        except RateLimitError as e:
            if attempt < config.max_attempts - 1:
                wait_time = e.retry_after if e.retry_after else config.strategy.get_wait_time(attempt)
                logger.warning(
                    f"{func.__name__} rate limited, waiting {wait_time}s "
                    f"(attempt {attempt + 1}/{config.max_attempts})"
                )
                
                if config.on_retry:
                    if asyncio.iscoroutinefunction(config.on_retry):
                        await config.on_retry(attempt, e, wait_time)
                    else:
                        config.on_retry(attempt, e, wait_time)
                
                await asyncio.sleep(wait_time)
                last_exception = e
            else:
                last_exception = e
                break
                
        except config.retryable_exceptions as e:
            last_exception = e
            
            if attempt < config.max_attempts - 1:
                wait_time = config.strategy.get_wait_time(attempt)
                logger.warning(
                    f"{func.__name__} failed with {type(e).__name__}: {e}, "
                    f"retrying in {wait_time}s (attempt {attempt + 1}/{config.max_attempts})"
                )
                
                if config.on_retry:
                    if asyncio.iscoroutinefunction(config.on_retry):
                        await config.on_retry(attempt, e, wait_time)
                    else:
                        config.on_retry(attempt, e, wait_time)
                
                await asyncio.sleep(wait_time)
            else:
                break
    
    logger.error(
        f"{func.__name__} failed after {config.max_attempts} attempts: {last_exception}"
    )
    
    if config.on_failure:
        if asyncio.iscoroutinefunction(config.on_failure):
            await config.on_failure(last_exception)
        else:
            config.on_failure(last_exception)
    
    raise last_exception


class CircuitBreaker:
    """Circuit breaker pattern for preventing cascading failures."""
    
    def __init__(
        self,
        failure_threshold: int = 5,
        recovery_timeout: float = 60.0,
        expected_exception: Type[Exception] = Exception
    ):
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        self.expected_exception = expected_exception
        
        self.failure_count = 0
        self.last_failure_time = None
        self.state = "closed"  # closed, open, half-open
    
    def call(self, func: Callable, *args, **kwargs) -> Any:
        """Call function with circuit breaker protection.
        
        Args:
            func: Function to call
            *args: Function arguments
            **kwargs: Function keyword arguments
        
        Returns:
            Function result
        
        Raises:
            Exception if circuit is open or function fails
        """
        if self.state == "open":
            if self._should_attempt_reset():
                self.state = "half-open"
            else:
                raise Exception(f"Circuit breaker is open for {func.__name__}")
        
        try:
            result = func(*args, **kwargs)
            self._on_success()
            return result
            
        except self.expected_exception as e:
            self._on_failure()
            raise
    
    def _should_attempt_reset(self) -> bool:
        """Check if circuit breaker should attempt reset."""
        if self.last_failure_time is None:
            return True
        
        return time.time() - self.last_failure_time >= self.recovery_timeout
    
    def _on_success(self) -> None:
        """Handle successful call."""
        if self.state == "half-open":
            self.state = "closed"
            self.failure_count = 0
            logger.info("Circuit breaker reset to closed")
    
    def _on_failure(self) -> None:
        """Handle failed call."""
        self.failure_count += 1
        self.last_failure_time = time.time()
        
        if self.failure_count >= self.failure_threshold:
            self.state = "open"
            logger.warning(
                f"Circuit breaker opened after {self.failure_count} failures"
            )
        elif self.state == "half-open":
            self.state = "open"
            logger.warning("Circuit breaker reopened after failure in half-open state")


def retry_with_backoff(
    func: Callable,
    max_attempts: int = 3,
    base_delay: float = 1.0,
    max_delay: float = 60.0
) -> Any:
    """Simple retry with exponential backoff helper.

    Args:
        func: Function to execute
        max_attempts: Maximum number of attempts
        base_delay: Base delay in seconds
        max_delay: Maximum delay in seconds

    Returns:
        Function result

    Raises:
        Last exception if all retries fail
    """
    strategy = ExponentialBackoff(base=base_delay, max_wait=max_delay)
    config = RetryConfig(
        max_attempts=max_attempts,
        strategy=strategy,
        retryable_exceptions=(RetryableError, Exception),
        non_retryable_exceptions=(NonRetryableError,)
    )

    return execute_with_retry(func, (), {}, config)


def with_timeout(timeout: float) -> Callable:
    """Decorator to add timeout to functions.
    
    Args:
        timeout: Timeout in seconds
    
    Returns:
        Decorated function with timeout
    """
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        async def async_wrapper(*args, **kwargs):
            try:
                return await asyncio.wait_for(
                    func(*args, **kwargs),
                    timeout=timeout
                )
            except asyncio.TimeoutError:
                logger.error(f"{func.__name__} timed out after {timeout}s")
                raise
        
        @functools.wraps(func)
        def sync_wrapper(*args, **kwargs):
            # For sync functions, we'd need threading or multiprocessing
            # This is a simplified version
            import signal
            
            def timeout_handler(signum, frame):
                raise TimeoutError(f"{func.__name__} timed out after {timeout}s")
            
            # Set the timeout handler
            signal.signal(signal.SIGALRM, timeout_handler)
            signal.alarm(int(timeout))
            
            try:
                result = func(*args, **kwargs)
                signal.alarm(0)  # Disable the alarm
                return result
            except TimeoutError:
                logger.error(f"{func.__name__} timed out after {timeout}s")
                raise
        
        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        else:
            # Note: signal-based timeout only works on Unix-like systems
            import platform
            if platform.system() == "Windows":
                logger.warning("Timeout decorator not fully supported on Windows for sync functions")
                return func
            return sync_wrapper
    
    return decorator