"""
LangSmith Configuration for Agent Tracing and Monitoring
Enables detailed tracing of agent executions, token usage, and performance metrics
"""

import os
import logging
from typing import Dict, Any, Optional, Callable
from functools import wraps
from datetime import datetime

from django.conf import settings

logger = logging.getLogger(__name__)

# LangSmith configuration
LANGSMITH_ENABLED = os.getenv('LANGSMITH_ENABLED', 'false').lower() == 'true'
LANGSMITH_API_KEY = os.getenv('LANGSMITH_API_KEY', '')
LANGSMITH_PROJECT = os.getenv('LANGSMITH_PROJECT', 'ai-smart-flight-agent')
LANGSMITH_ENDPOINT = os.getenv('LANGSMITH_ENDPOINT', 'https://api.smith.langchain.com')


def init_langsmith():
    """Initialize LangSmith tracing"""
    try:
        if not LANGSMITH_ENABLED or not LANGSMITH_API_KEY:
            logger.info("LangSmith tracing is disabled")
            return False

        # Set environment variables for LangChain
        os.environ['LANGCHAIN_TRACING_V2'] = 'true'
        os.environ['LANGCHAIN_API_KEY'] = LANGSMITH_API_KEY
        os.environ['LANGCHAIN_PROJECT'] = LANGSMITH_PROJECT
        os.environ['LANGCHAIN_ENDPOINT'] = LANGSMITH_ENDPOINT

        logger.info(f"LangSmith tracing enabled for project: {LANGSMITH_PROJECT}")
        return True

    except Exception as e:
        logger.error(f"Error initializing LangSmith: {str(e)}")
        return False


def trace_agent_execution(agent_name: str, operation: str = "execute"):
    """
    Decorator to trace agent executions with LangSmith.

    Args:
        agent_name: Name of the agent being traced
        operation: Operation being performed

    Usage:
        @trace_agent_execution("FlightAgent", "search_flights")
        def search_flights(self, origin, destination):
            ...
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs):
            if not LANGSMITH_ENABLED:
                return func(*args, **kwargs)

            try:
                from langsmith import traceable

                # Create a traceable version of the function
                traced_func = traceable(
                    run_type="chain",
                    name=f"{agent_name}.{operation}",
                    metadata={
                        'agent': agent_name,
                        'operation': operation,
                        'timestamp': datetime.now().isoformat()
                    }
                )(func)

                return traced_func(*args, **kwargs)

            except ImportError:
                logger.warning("langsmith package not installed, skipping tracing")
                return func(*args, **kwargs)
            except Exception as e:
                logger.error(f"Error in tracing: {str(e)}")
                return func(*args, **kwargs)

        return wrapper
    return decorator


def log_agent_metrics(
    agent_name: str,
    operation: str,
    duration_seconds: float,
    token_usage: Optional[Dict[str, int]] = None,
    cost_usd: Optional[float] = None,
    success: bool = True,
    error: Optional[str] = None
) -> None:
    """
    Log agent execution metrics to LangSmith.

    Args:
        agent_name: Name of the agent
        operation: Operation performed
        duration_seconds: Execution duration
        token_usage: Token usage stats (prompt_tokens, completion_tokens, total_tokens)
        cost_usd: Estimated cost in USD
        success: Whether operation succeeded
        error: Error message if failed
    """
    try:
        if not LANGSMITH_ENABLED:
            return

        from langsmith import Client

        client = Client(api_key=LANGSMITH_API_KEY, api_url=LANGSMITH_ENDPOINT)

        # Create feedback/metrics entry
        metrics = {
            'agent': agent_name,
            'operation': operation,
            'duration_seconds': duration_seconds,
            'success': success,
            'timestamp': datetime.now().isoformat()
        }

        if token_usage:
            metrics['token_usage'] = token_usage

        if cost_usd:
            metrics['estimated_cost_usd'] = cost_usd

        if error:
            metrics['error'] = error

        # Log metrics (you can also use client.create_feedback for more detailed tracking)
        logger.info(f"Agent metrics: {metrics}")

    except Exception as e:
        logger.error(f"Error logging agent metrics: {str(e)}")


class AgentPerformanceMonitor:
    """Monitor and track agent performance metrics"""

    def __init__(self):
        self.metrics = []

    def record_execution(
        self,
        agent_name: str,
        operation: str,
        duration_seconds: float,
        token_usage: Optional[Dict[str, int]] = None,
        success: bool = True,
        error: Optional[str] = None
    ) -> None:
        """Record an agent execution"""
        metric = {
            'agent': agent_name,
            'operation': operation,
            'duration_seconds': duration_seconds,
            'token_usage': token_usage or {},
            'success': success,
            'error': error,
            'timestamp': datetime.now().isoformat()
        }

        self.metrics.append(metric)

        # Also log to LangSmith if enabled
        log_agent_metrics(
            agent_name=agent_name,
            operation=operation,
            duration_seconds=duration_seconds,
            token_usage=token_usage,
            success=success,
            error=error
        )

    def get_summary(self) -> Dict[str, Any]:
        """Get summary of all recorded metrics"""
        if not self.metrics:
            return {}

        total_executions = len(self.metrics)
        successful = sum(1 for m in self.metrics if m['success'])
        failed = total_executions - successful

        total_duration = sum(m['duration_seconds'] for m in self.metrics)
        avg_duration = total_duration / total_executions if total_executions > 0 else 0

        total_tokens = sum(
            m['token_usage'].get('total_tokens', 0)
            for m in self.metrics
            if m.get('token_usage')
        )

        # Group by agent
        by_agent = {}
        for metric in self.metrics:
            agent = metric['agent']
            if agent not in by_agent:
                by_agent[agent] = {
                    'executions': 0,
                    'successful': 0,
                    'failed': 0,
                    'total_duration': 0,
                    'total_tokens': 0
                }

            by_agent[agent]['executions'] += 1
            if metric['success']:
                by_agent[agent]['successful'] += 1
            else:
                by_agent[agent]['failed'] += 1
            by_agent[agent]['total_duration'] += metric['duration_seconds']
            by_agent[agent]['total_tokens'] += metric.get('token_usage', {}).get('total_tokens', 0)

        return {
            'total_executions': total_executions,
            'successful': successful,
            'failed': failed,
            'success_rate': successful / total_executions if total_executions > 0 else 0,
            'total_duration_seconds': total_duration,
            'average_duration_seconds': avg_duration,
            'total_tokens': total_tokens,
            'by_agent': by_agent,
            'generated_at': datetime.now().isoformat()
        }

    def clear_metrics(self) -> None:
        """Clear all recorded metrics"""
        self.metrics = []


# Global performance monitor instance
_performance_monitor = None


def get_performance_monitor() -> AgentPerformanceMonitor:
    """Get or create global performance monitor"""
    global _performance_monitor
    if _performance_monitor is None:
        _performance_monitor = AgentPerformanceMonitor()
    return _performance_monitor


# Initialize LangSmith on module import
if LANGSMITH_ENABLED:
    init_langsmith()
