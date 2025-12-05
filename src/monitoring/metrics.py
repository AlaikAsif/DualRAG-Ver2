"""Performance metrics tracking and collection."""

import time
import logging
from typing import Dict, Any, Optional
from dataclasses import dataclass, field, asdict
from datetime import datetime
import psutil
import os

logger = logging.getLogger(__name__)


@dataclass
class ExecutionMetrics:
    """Metrics for a single execution."""
    component: str
    operation: str
    start_time: float = field(default_factory=time.time)
    end_time: Optional[float] = None
    duration_ms: float = 0.0
    input_size: int = 0
    output_size: int = 0
    memory_used_mb: float = 0.0
    error: Optional[str] = None
    status: str = "running"
    
    def complete(self, error: Optional[str] = None):
        """Mark execution as complete."""
        self.end_time = time.time()
        self.duration_ms = (self.end_time - self.start_time) * 1000
        self.status = "error" if error else "success"
        self.error = error
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for logging."""
        return asdict(self)


class MetricsCollector:
    """Collect and aggregate metrics across system."""
    
    def __init__(self):
        """Initialize metrics collector."""
        self.metrics: Dict[str, list] = {}
        self.process = psutil.Process(os.getpid())
    
    def start_metric(
        self, 
        component: str, 
        operation: str
    ) -> ExecutionMetrics:
        """
        Start tracking a metric.
        
        Args:
            component: Component name (e.g., 'retrieval', 'llm', 'embeddings')
            operation: Operation name (e.g., 'retrieve', 'generate_response')
            
        Returns:
            ExecutionMetrics instance to track execution
        """
        metric = ExecutionMetrics(component=component, operation=operation)
        
        if component not in self.metrics:
            self.metrics[component] = []
        
        logger.debug(f"Starting metric: {component}.{operation}")
        return metric
    
    def record_metric(
        self, 
        metric: ExecutionMetrics,
        input_size: int = 0,
        output_size: int = 0,
        error: Optional[str] = None
    ):
        """
        Record a completed metric.
        
        Args:
            metric: ExecutionMetrics instance to record
            input_size: Size of input data
            output_size: Size of output data
            error: Error message if execution failed
        """
        metric.input_size = input_size
        metric.output_size = output_size
        metric.memory_used_mb = self.process.memory_info().rss / 1024 / 1024
        metric.complete(error)
        
        component = metric.component
        if component not in self.metrics:
            self.metrics[component] = []
        
        self.metrics[component].append(metric)
        
        log_level = logging.ERROR if error else logging.INFO
        logger.log(
            log_level,
            f"[Metrics] {component}.{metric.operation} - "
            f"Status: {metric.status}, Duration: {metric.duration_ms:.2f}ms, "
            f"Memory: {metric.memory_used_mb:.2f}MB"
        )
    
    def get_metrics(self, component: Optional[str] = None) -> Dict[str, Any]:
        """
        Get collected metrics.
        
        Args:
            component: Optional component to filter by
            
        Returns:
            Dictionary of metrics
        """
        if component:
            return {
                component: [m.to_dict() for m in self.metrics.get(component, [])]
            }
        
        return {
            comp: [m.to_dict() for m in metrics]
            for comp, metrics in self.metrics.items()
        }
    
    def get_summary(self, component: Optional[str] = None) -> Dict[str, Any]:
        """
        Get summary statistics of metrics.
        
        Args:
            component: Optional component to filter by
            
        Returns:
            Summary statistics
        """
        metrics_to_summarize = {}
        
        if component:
            metrics_to_summarize = {
                component: self.metrics.get(component, [])
            }
        else:
            metrics_to_summarize = self.metrics
        
        summary = {}
        
        for comp, metrics_list in metrics_to_summarize.items():
            if not metrics_list:
                continue
            
            durations = [m.duration_ms for m in metrics_list if m.status == "success"]
            errors = [m for m in metrics_list if m.status == "error"]
            
            summary[comp] = {
                "total_executions": len(metrics_list),
                "successful": len(durations),
                "errors": len(errors),
                "avg_duration_ms": sum(durations) / len(durations) if durations else 0,
                "min_duration_ms": min(durations) if durations else 0,
                "max_duration_ms": max(durations) if durations else 0,
                "avg_input_size": sum(m.input_size for m in metrics_list) / len(metrics_list) if metrics_list else 0,
                "avg_output_size": sum(m.output_size for m in metrics_list) / len(metrics_list) if metrics_list else 0,
                "error_messages": [m.error for m in errors],
            }
        
        return summary
    
    def clear_metrics(self, component: Optional[str] = None):
        """
        Clear collected metrics.
        
        Args:
            component: Optional component to clear, or all if None
        """
        if component:
            self.metrics[component] = []
            logger.info(f"Cleared metrics for {component}")
        else:
            self.metrics.clear()
            logger.info("Cleared all metrics")


# Global metrics collector instance
_metrics_collector: Optional[MetricsCollector] = None


def get_metrics_collector() -> MetricsCollector:
    """Get or create global metrics collector."""
    global _metrics_collector
    if _metrics_collector is None:
        _metrics_collector = MetricsCollector()
    return _metrics_collector


def start_metric(component: str, operation: str) -> ExecutionMetrics:
    """
    Start tracking a metric.
    
    Args:
        component: Component name
        operation: Operation name
        
    Returns:
        ExecutionMetrics instance
    """
    collector = get_metrics_collector()
    return collector.start_metric(component, operation)


def record_metric(
    metric: ExecutionMetrics,
    input_size: int = 0,
    output_size: int = 0,
    error: Optional[str] = None
):
    """
    Record a completed metric.
    
    Args:
        metric: ExecutionMetrics to record
        input_size: Input size
        output_size: Output size
        error: Optional error message
    """
    collector = get_metrics_collector()
    collector.record_metric(metric, input_size, output_size, error)
