"""Metrics configuration and persistence module."""

from collections.abc import Callable
from functools import wraps
from pathlib import Path
from typing import Any

import sentry_sdk

# Sentry DSN for error reporting
SENTRY_DSN = "https://a545ee7ae82d1c7055e7b53633ba691c@o4510280629420032.ingest.us.sentry.io/4510280631320576"

# Global flags to track metrics and enhanced error reporting
_metrics_enabled = False
_enhanced_error_reporting_enabled = False


def get_metrics_config_path() -> Path:
    """
    Get the path to the metrics configuration file.

    Returns:
        Path to ~/.slither-mcp/metrics_disabled
    """
    return Path.home() / ".slither-mcp" / "metrics_disabled"


def is_metrics_disabled() -> bool:
    """
    Check if metrics have been permanently disabled by the user.

    Returns:
        True if metrics are disabled, False otherwise
    """
    return get_metrics_config_path().exists()


def disable_metrics_permanently() -> None:
    """
    Permanently disable metrics by creating the metrics_disabled file.

    This creates the ~/.slither-mcp directory if it doesn't exist,
    then creates an empty metrics_disabled file.
    """
    config_path = get_metrics_config_path()
    config_path.parent.mkdir(parents=True, exist_ok=True)
    config_path.touch()


def is_metrics_enabled() -> bool:
    """Check if metrics are currently enabled."""
    return _metrics_enabled


def is_enhanced_error_reporting_enabled() -> bool:
    """Check if enhanced error reporting is currently enabled."""
    return _enhanced_error_reporting_enabled


def _create_before_send_hook() -> Callable:
    """
    Create a before_send hook for Sentry that filters events.

    Returns:
        A before_send function that can be used with sentry_sdk.init
    """

    def before_send(event, hint):
        """
        Filter Sentry events before sending.

        Only send exceptions if enhanced_error_reporting_enabled is True.
        Always allow messages (metrics events).
        Strip sensitive information (server_name, argv).
        """
        # Strip server_name and sys.argv for privacy
        if "server_name" in event:
            del event["server_name"]

        if "contexts" in event and "runtime" in event["contexts"]:
            if "sys.argv" in event["contexts"]["runtime"]:
                del event["contexts"]["runtime"]["sys.argv"]

        # Allow all message events (metrics)
        if event.get("level") == "info" or not hint.get("exc_info"):
            return event

        # Only send exceptions if enhanced error reporting is enabled
        if _enhanced_error_reporting_enabled:
            return event

        # Drop exception events if enhanced error reporting is not enabled
        return None

    return before_send


def initialize_metrics(enable_enhanced_error_reporting: bool = False) -> None:
    """
    Initialize Sentry metrics.

    Args:
        enable_enhanced_error_reporting: Whether to enable enhanced error reporting
    """
    global _metrics_enabled, _enhanced_error_reporting_enabled

    _metrics_enabled = True
    _enhanced_error_reporting_enabled = enable_enhanced_error_reporting

    sentry_sdk.init(
        dsn=SENTRY_DSN,
        traces_sample_rate=1.0,
        profiles_sample_rate=1.0,
        environment="production",
        release="slither-mcp@0.2.0",
        before_send=_create_before_send_hook(),
        # Disable default error capturing - we'll handle it explicitly
        default_integrations=False,
    )


def track_tool_call(tool_name: str) -> Callable:
    """
    Decorator to track tool calls and exceptions with Sentry.

    Tracks:
    - Tool call events (when metrics enabled)
    - Success/failure status (when metrics enabled)
    - Exceptions (when enhanced error reporting enabled)

    Args:
        tool_name: Name of the tool being tracked

    Returns:
        Decorator function
    """

    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            # Log tool call
            if _metrics_enabled:
                sentry_sdk.capture_message(
                    f"tool_call_{tool_name}", level="info", extras={"tool_name": tool_name}
                )

            try:
                result = func(*args, **kwargs)

                # Log success/failure
                if _metrics_enabled and hasattr(result, "success"):
                    status = "success" if result.success else "failure"
                    sentry_sdk.capture_message(
                        f"tool_{status}_{tool_name}", level="info", extras={"tool_name": tool_name}
                    )

                return result

            except Exception as e:
                # Log exception details if enhanced error reporting enabled
                if _enhanced_error_reporting_enabled:
                    sentry_sdk.capture_exception(e)

                # Log exception event if metrics enabled
                if _metrics_enabled:
                    sentry_sdk.capture_message(
                        f"tool_exception_{tool_name}",
                        level="error",
                        extras={"tool_name": tool_name},
                    )

                raise

        return wrapper

    return decorator
