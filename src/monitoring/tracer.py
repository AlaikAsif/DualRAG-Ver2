"""
Chain Execution Tracing and Monitoring.

Provides decorators for tracing chain execution, measuring latency,
and collecting metrics about chain performance.
"""

import time
import functools
from typing import Any, Callable, Optional, Dict
from src.monitoring.logger import get_logger

logger = get_logger(__name__)


def trace_chain_execution(
    chain_name: str = "unknown",
    log_args: bool = False,
    log_result: bool = False,
):
    """
    Decorator to trace chain execution with timing and logging.
    
    Args:
        chain_name: Name of the chain for logging
        log_args: Whether to log function arguments
        log_result: Whether to log the result
    
    Returns:
        Decorated function with execution tracing
    
    Example:
        @trace_chain_execution(chain_name="static_rag")
        def retrieve_documents(self, query: str):
            ...
    """
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs) -> Any:
            start_time = time.time()
            func_name = func.__name__
            full_name = f"{chain_name}.{func_name}"
            
            # Log entry
            log_msg = f"[TRACE] Entering {full_name}"
            if log_args:
                log_msg += f" | args={args[1:] if args else ()} | kwargs={kwargs}"
            logger.debug(log_msg)
            
            try:
                # Execute function
                result = func(*args, **kwargs)
                
                # Calculate elapsed time
                elapsed_ms = (time.time() - start_time) * 1000
                
                # Log exit
                log_msg = f"[TRACE] Exiting {full_name} | elapsed={elapsed_ms:.2f}ms"
                if log_result:
                    log_msg += f" | result_type={type(result).__name__}"
                logger.debug(log_msg)
                
                return result
            
            except Exception as e:
                elapsed_ms = (time.time() - start_time) * 1000
                logger.error(
                    f"[TRACE] Exception in {full_name} after {elapsed_ms:.2f}ms: {e}",
                    exc_info=True
                )
                raise
        
        return wrapper
    return decorator


def trace_metrics(metric_name: str = "unknown"):
    """
    Decorator to collect and log performance metrics.
    
    Args:
        metric_name: Name of the metric being tracked
    
    Returns:
        Decorated function that collects timing metrics
    """
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs) -> Any:
            start_time = time.time()
            start_memory = None
            
            try:
                import psutil
                process = psutil.Process()
                start_memory = process.memory_info().rss / 1024 / 1024  # MB
            except ImportError:
                pass
            
            try:
                result = func(*args, **kwargs)
                elapsed_ms = (time.time() - start_time) * 1000
                
                log_msg = f"[METRIC] {metric_name} | elapsed={elapsed_ms:.2f}ms"
                if start_memory is not None:
                    try:
                        end_memory = psutil.Process().memory_info().rss / 1024 / 1024
                        memory_delta = end_memory - start_memory
                        log_msg += f" | memory_delta={memory_delta:.2f}MB"
                    except:
                        pass
                
                logger.info(log_msg)
                return result
            
            except Exception as e:
                elapsed_ms = (time.time() - start_time) * 1000
                logger.error(f"[METRIC] {metric_name} FAILED after {elapsed_ms:.2f}ms: {e}")
                raise
        
        return wrapper
    return decorator
